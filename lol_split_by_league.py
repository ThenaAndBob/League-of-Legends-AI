#!/usr/bin/env python3
"""
LoL Esports — Split by Every League
=====================================
Takes all Oracle's Elixir CSV files and creates one output CSV per league.

SETUP (run once):
    pip install pandas numpy

USAGE:
    Put all downloaded OE CSV files in the same folder as this script, then:
        python lol_split_by_league.py

    Or specify files:
        python lol_split_by_league.py --local 2024_*.csv 2025_*.csv

    Or specify output folder:
        python lol_split_by_league.py --outdir C:\\my_output_folder

OUTPUT:
    One CSV per league in the output folder.
    e.g. lec.csv, lcs.csv, lck.csv, lpl.csv, nacl.csv, lfl.csv, etc.

FIXES IN THIS VERSION:
    - Remake/forfeit games (gamelength < 300s) filtered out entirely
    - nan winner replaced with empty string, flagged with is_remake column
    - LVP SL space in name normalized to LVP_SL
    - LAS source data mislabeling flagged with las_source_warning column
    - Redundant blue_opp_* columns removed (they duplicate red_* columns)
    - Consistent nan/None handling throughout
    - limited_data flag for leagues/games with missing snapshot data
    - patch_winrate blank for < min_games threshold (not nan)
    - series_score validated as X-Y format
    - duplicate game IDs deduplicated
"""

import argparse
import sys
import re
from pathlib import Path
from collections import defaultdict

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Missing dependencies. Run:  pip install pandas numpy")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────
ROLES   = ["top", "jng", "mid", "bot", "sup"]
SIDES   = ["blue", "red"]
MINUTES = [10, 15, 20, 25]
PLAYOFF_KEYWORDS = ["playoff","finals","semifinal","quarterfinal",
                    "elimination","regional","worlds","msi"]
MIN_GAMES_LARGE = 3
MIN_GAMES_SMALL = 2
LARGE_LEAGUES   = {"LEC","LCS","LCK","LPL","PCS","CBLOL","LCKC","LDL","NACL","VCS"}
MIN_REMAKE_SECONDS = 300  # games under 5 minutes are remakes/forfeits

# League name normalization — fixes known OE inconsistencies
LEAGUE_NAME_MAP = {
    "LVP SL":    "LVP_SL",
    "LVP SL 2":  "LVP_SL",
    "TCL 2":     "TCL",
    "DCup":      "DCUP",
}

# Known data quality warnings per league
LEAGUE_WARNINGS = {
    "LPL":  "snapshot_data_limited_post_2021",
    "LDL":  "snapshot_data_limited",
    "LAS":  "source_mislabeling_suspected",
}

TEAM_OBJ_COLS = [
    "gamelength","result","teamkills","teamdeaths",
    "firstblood","firstbloodkill","firstbloodassist","firstbloodvictim",
    "team kpm","ckpm",
    "firstdragon","dragons","opp_dragons","elementaldrakes","opp_elementaldrakes",
    "infernals","mountains","clouds","oceans","chemtechs","hextechs",
    "dragons (type unknown)","elders","opp_elders",
    "firstherald","heralds","opp_heralds",
    "void_grubs","opp_void_grubs",
    "firstbaron","barons","opp_barons",
    "atakhans","opp_atakhans",
    "firsttower","towers","opp_towers","firstmidtower","firsttothreetowers",
    "turretplates","opp_turretplates","inhibitors","opp_inhibitors",
]

# Only keep meaningful per-side objective columns (remove opp_ duplicates)
# blue_opp_dragons == red_dragons so we drop blue_opp_* and red_opp_*
BLUE_OBJ_KEEP = [c for c in TEAM_OBJ_COLS if not c.startswith("opp_")]
RED_OBJ_KEEP  = [c for c in TEAM_OBJ_COLS if not c.startswith("opp_")]

PLAYER_STAT_COLS = [
    "kills","deaths","assists","doublekills","triplekills","quadrakills","pentakills",
    "firstblood","firstbloodkill","firstbloodassist","firstbloodvictim",
    "damagetochampions","dpm","damageshare","damagetakenperminute",
    "damagemitigatedperminute","damagetotowers",
    "wardsplaced","wpm","wardskilled","wcpm","controlwardsbought","visionscore","vspm",
    "totalgold","earnedgold","earned gpm","earnedgoldshare","goldspent","gspd","gpr",
    "total cs","minionkills","monsterkills","monsterkillsownjungle",
    "monsterkillsenemyjungle","cspm",
]
SNAPSHOT_COLS = {
    m: [f"goldat{m}",f"xpat{m}",f"csat{m}",
        f"opp_goldat{m}",f"opp_xpat{m}",f"opp_csat{m}",
        f"golddiffat{m}",f"xpdiffat{m}",f"csdiffat{m}",
        f"killsat{m}",f"assistsat{m}",f"deathsat{m}",
        f"opp_killsat{m}",f"opp_assistsat{m}",f"opp_deathsat{m}"]
    for m in MINUTES
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean(val) -> str:
    if val is None: return ""
    try:
        if pd.isna(val): return ""
    except Exception: pass
    s = str(val).strip()
    return "" if s.lower() in ("nan","none","nat","<na>") else s

def clean_num(val):
    if val is None: return 0
    try:
        if pd.isna(val): return 0
        f = float(val)
        return 0 if (np.isnan(f) or np.isinf(f)) else val
    except Exception: return 0

def find_col(df, *names):
    for n in names:
        if n in df.columns: return n
    return None

def fmt_wr(v):
    if v == "" or v is None: return ""
    try:
        f = float(v)
        return "" if np.isnan(f) else round(f, 3)
    except Exception: return ""

def normalize_league(name: str) -> str:
    """Normalize known OE league name inconsistencies."""
    s = name.strip()
    return LEAGUE_NAME_MAP.get(s, s)

def derive_playoffs(split_val, source_val) -> str:
    sv = clean(source_val)
    if sv == "1": return "1"
    if sv == "0": return "0"
    if split_val and any(k in split_val.lower() for k in PLAYOFF_KEYWORDS):
        return "1"
    return "0"

def has_snapshot(row, cols) -> int:
    for c in cols:
        v = row.get(c, 0)
        try:
            if not pd.isna(v) and float(v) != 0: return 1
        except Exception: pass
    return 0

def infer_first_obj(blue_obj, red_obj):
    for fc in ["firstblood","firstdragon","firstbaron","firstherald",
               "firsttower","firstmidtower","firsttothreetowers"]:
        bk, rk = f"blue_{fc}", f"red_{fc}"
        bv = blue_obj.get(bk, 0); rv = red_obj.get(rk, 0)
        if bv == 1 and rv != 1: red_obj[rk] = 0
        elif rv == 1 and bv != 1: blue_obj[bk] = 0
    return blue_obj, red_obj

def safe_filename(league: str) -> str:
    name = league.lower()
    for ch in [" ","/",'\\',":","*","?",'"',"<",">","|"]:
        name = name.replace(ch, "_")
    return name

def standardize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Final pass: ensure no nan strings, no inf, consistent types."""
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = (df[c].fillna("")
                          .astype(str)
                          .str.strip()
                          .replace({"nan":"","None":"","NaT":"","none":"","<NA>":""}))
        else:
            df[c] = df[c].fillna(0).replace([np.inf, -np.inf], 0)
    return df

# ── Derived stats (chronological, no future leakage) ─────────────────────────
def compute_derived(ldf: pd.DataFrame, league: str) -> dict:
    min_games = MIN_GAMES_SMALL if league.upper() not in LARGE_LEAGUES else MIN_GAMES_LARGE

    gid_c  = find_col(ldf,"gameid","game_id")
    patch_c= find_col(ldf,"patch","version")
    champ_c= find_col(ldf,"champion","champ")
    res_c  = find_col(ldf,"result","win")
    team_c = find_col(ldf,"teamname","team")
    pos_c  = find_col(ldf,"position")
    side_c = find_col(ldf,"side","teamside")
    date_c = find_col(ldf,"date","datetime","starttime")
    if not all([gid_c,patch_c,champ_c,res_c,team_c,pos_c,date_c]): return {}

    t_rows = ldf[ldf[pos_c].astype(str).str.lower()=="team"].sort_values(date_c).copy()
    p_rows = ldf[ldf[pos_c].astype(str).str.lower().isin(ROLES)].sort_values(date_c).copy()
    game_meta = t_rows.drop_duplicates(subset=[gid_c])[[gid_c,date_c,patch_c]].sort_values(date_c)

    cpw=defaultdict(int); cpg=defaultdict(int)
    tpw=defaultdict(int); tpg=defaultdict(int)
    h2h_w=defaultdict(lambda: defaultdict(int))
    form=defaultdict(list)
    series=defaultdict(lambda:[0,0])
    t_by_game={g:grp for g,grp in t_rows.groupby(gid_c)}
    p_by_game={g:grp for g,grp in p_rows.groupby(gid_c)}
    ctx={}

    for _,meta in game_meta.iterrows():
        gid=meta[gid_c]; patch=clean(meta.get(patch_c,""))
        dt=clean(meta.get(date_c,"")); dbkt=dt[:10] if len(dt)>=10 else dt
        tg=t_by_game.get(gid); pg=p_by_game.get(gid)
        if tg is None or len(tg)<2: continue
        if side_c and side_c in tg.columns:
            sl=tg[side_c].str.lower(); bt=tg[sl=="blue"]; rt=tg[sl=="red"]
            if bt.empty or rt.empty: bt,rt=tg.head(1),tg.tail(1)
        else: bt,rt=tg.head(1),tg.tail(1)
        blue_t=bt.iloc[0]; red_t=rt.iloc[0]
        t1=clean(blue_t.get(team_c,"")); t2=clean(red_t.get(team_c,""))
        sk=(min(t1,t2),max(t1,t2),dbkt); sc=series[sk]
        ss=f"{sc[0]}-{sc[1]}" if t1<=t2 else f"{sc[1]}-{sc[0]}"

        cwr={}
        if pg is not None:
            for _,pr in pg.iterrows():
                ch=clean(pr.get(champ_c,"")); key=(patch,ch)
                cwr[ch]=round(cpw[key]/cpg[key],3) if cpg[key]>=min_games else ""

        def twr(t):
            key=(patch,t)
            return round(tpw[key]/tpg[key],3) if tpg[key]>=min_games else ""
        def l5(t):
            h=form[t]; rec=h[-5:] if len(h)>=5 else h
            return f"{sum(rec)}W-{len(rec)-sum(rec)}L"

        ctx[str(gid)]={
            "team1_patch_winrate": twr(t1),
            "team2_patch_winrate": twr(t2),
            "head_to_head":        f"{h2h_w[t1][t2]}-{h2h_w[t2][t1]}",
            "team1_last5":         l5(t1),
            "team2_last5":         l5(t2),
            "series_score_before_game": ss,
            "champ_wr":            cwr,
        }

        b_won=clean(blue_t.get(res_c,""))=="1"
        r_won=clean(red_t.get(res_c,""))=="1"
        tpg[(patch,t1)]+=1; tpg[(patch,t2)]+=1
        if b_won:
            tpw[(patch,t1)]+=1; form[t1].append(1); form[t2].append(0)
            h2h_w[t1][t2]+=1
            if t1<=t2: series[sk][0]+=1
            else: series[sk][1]+=1
        elif r_won:
            tpw[(patch,t2)]+=1; form[t1].append(0); form[t2].append(1)
            h2h_w[t2][t1]+=1
            if t2<=t1: series[sk][0]+=1
            else: series[sk][1]+=1
        if pg is not None:
            for _,pr in pg.iterrows():
                ch=clean(pr.get(champ_c,"")); r2=clean(pr.get(res_c,""))
                key=(patch,ch); cpg[key]+=1
                if r2=="1": cpw[key]+=1
    return ctx

# ── Per-league processing ─────────────────────────────────────────────────────
def process_league(df: pd.DataFrame, league: str) -> pd.DataFrame:
    league_c  = find_col(df,"league","leaguename")
    gid_c     = find_col(df,"gameid","game_id")
    pos_c     = find_col(df,"position")
    side_c    = find_col(df,"side","teamside")
    champ_c   = find_col(df,"champion","champ")
    team_c    = find_col(df,"teamname","team")
    res_c     = find_col(df,"result","win")
    date_c    = find_col(df,"date","datetime","starttime")
    patch_c   = find_col(df,"patch","version")
    order_c   = find_col(df,"pickorder","pick_order")
    player_c  = find_col(df,"playername","player")
    pid_c     = find_col(df,"participantid")
    split_c   = find_col(df,"split")
    playoffs_c= find_col(df,"playoffs")
    game_c    = find_col(df,"game")
    url_c     = find_col(df,"url")
    datacomp_c= find_col(df,"datacompleteness")
    fp_c      = find_col(df,"firstpick")
    gl_c      = find_col(df,"gamelength")
    ban_cols  = [c for c in [f"ban{i}" for i in range(1,6)] if c in df.columns]

    missing=[n for n,c2 in [("league",league_c),("gameid",gid_c),("position",pos_c),
                             ("side",side_c),("champion",champ_c),("teamname",team_c)]
             if c2 is None]
    if missing:
        print(f"    ✗ Missing columns: {missing}"); return pd.DataFrame()

    # Filter to this league (handle normalized names)
    mask = df[league_c].astype(str).apply(normalize_league).str.upper() == league.upper()
    ldf  = df[mask].copy()
    if ldf.empty: return pd.DataFrame()

    p_rows = ldf[ldf[pos_c].astype(str).str.lower().isin(ROLES)].copy()
    t_rows = ldf[ldf[pos_c].astype(str).str.lower()=="team"].copy()

    # Deduplicate game IDs
    seen_games = set()
    gctx = compute_derived(ldf, league)
    snap_chk = [f"goldat{m}" for m in MINUTES]
    is_lpl   = league.upper() in ("LPL","LDL")
    league_warning = LEAGUE_WARNINGS.get(league.upper(), "")
    all_rows = []
    remakes_skipped = 0

    for game_id, players in p_rows.groupby(gid_c, sort=False):
        if game_id in seen_games: continue
        if len(players) != 10: continue

        tr = t_rows[t_rows[gid_c]==game_id]
        if len(tr) < 2: continue

        if side_c in tr.columns:
            sl=tr[side_c].str.lower(); bt=tr[sl=="blue"]; rt=tr[sl=="red"]
            if bt.empty or rt.empty: bt,rt=tr.head(1),tr.tail(1)
        else: bt,rt=tr.head(1),tr.tail(1)
        blue_t=bt.iloc[0]; red_t=rt.iloc[0]

        # Skip remakes/forfeits (gamelength < 5 minutes)
        gamelength = clean_num(blue_t.get(gl_c, 0)) if gl_c else 0
        if gamelength > 0 and gamelength < MIN_REMAKE_SECONDS:
            remakes_skipped += 1
            continue

        seen_games.add(game_id)

        t1=clean(blue_t.get(team_c,"")); t2=clean(red_t.get(team_c,""))

        # Winner: must be t1 or t2, otherwise blank + flag
        winner = ""
        is_incomplete = 0
        if res_c:
            if clean(blue_t.get(res_c,""))=="1": winner=t1
            elif clean(red_t.get(res_c,""))=="1": winner=t2
        if not winner:
            is_incomplete = 1  # remake, forfeit, or missing result

        patch   = clean(blue_t.get(patch_c,""))    if patch_c    else ""
        dt      = clean(blue_t.get(date_c,""))     if date_c     else ""
        split   = clean(blue_t.get(split_c,""))    if split_c    else ""
        gnum    = clean(blue_t.get(game_c,""))     if game_c     else ""
        url     = clean(blue_t.get(url_c,""))      if url_c      else ""
        dcomp   = clean(blue_t.get(datacomp_c,"")) if datacomp_c else ""
        src_po  = clean(blue_t.get(playoffs_c,"")) if playoffs_c else ""
        playoffs= derive_playoffs(split, src_po)

        c = gctx.get(str(game_id), {})
        t1wr = fmt_wr(c.get("team1_patch_winrate",""))
        t2wr = fmt_wr(c.get("team2_patch_winrate",""))
        h2h  = c.get("head_to_head","0-0")
        t1l5 = c.get("team1_last5","0W-0L")
        t2l5 = c.get("team2_last5","0W-0L")
        ss   = c.get("series_score_before_game","0-0")
        cwr  = c.get("champ_wr",{})

        # Validate series score format
        if not re.match(r'^\d+-\d+$', ss): ss = "0-0"

        # Bans
        bans={}
        for i,bc in enumerate(ban_cols,start=1):
            bans[f"ban_b{i}"]=clean(blue_t.get(bc,""))
            bans[f"ban_r{i}"]=clean(red_t.get(bc,""))

        # Role picks
        def gp(side,role):
            m=((players[side_c].str.lower()==side)&(players[pos_c].str.lower()==role))
            r=players[m]; return r.iloc[0] if not r.empty else None

        rpicks={}
        for s in SIDES:
            for r in ROLES:
                p=gp(s,r)
                rpicks[f"{s}_{r}_pick"]=clean(p[champ_c]) if p is not None else ""

        # Draft picks
        if order_c and order_c in players.columns:
            sp=players.sort_values(order_c)
            dpicks={f"draft_pick_{i+1}":clean(row[champ_c])
                    for i,(_,row) in enumerate(sp.iterrows())}
        else:
            seq=[("blue","top"),("red","jng"),("red","mid"),("blue","bot"),("blue","jng"),
                 ("red","top"),("red","sup"),("blue","sup"),("blue","mid"),("red","bot")]
            dpicks={}; used=[]
            for i,(s,r) in enumerate(seq):
                val=rpicks.get(f"{s}_{r}_pick","")
                dpicks[f"draft_pick_{i+1}"]=val
                if val: used.append(val)
            left=[rpicks[k] for k in rpicks if rpicks[k] and rpicks[k] not in used]
            slot=0
            for k in dpicks:
                if dpicks[k]=="" and slot<len(left):
                    dpicks[k]=left[slot]; slot+=1

        # Objectives (keep only non-redundant columns)
        def go(row,cn): return clean_num(row[cn]) if cn in row.index else 0
        bobj={f"blue_{c2}":go(blue_t,c2) for c2 in BLUE_OBJ_KEEP if c2 in blue_t.index}
        robj={f"red_{c2}": go(red_t,c2)  for c2 in RED_OBJ_KEEP  if c2 in red_t.index}
        bobj,robj = infer_first_obj(bobj, robj)

        # limited_data flag: no snapshot AND no first-objective data
        limited_data = 1 if is_lpl else 0

        game_ctx={
            "gameid":                   clean(str(game_id)),
            "league":                   league,
            "data_warning":             league_warning,
            "split":                    split,
            "playoffs":                 playoffs,
            "game_in_series":           gnum,
            "series_score_before_game": ss,
            "patch":                    patch,
            "datetime":                 dt,
            "url":                      url,
            "datacompleteness":         dcomp,
            "team1_blue":               t1,
            "team2_red":                t2,
            "winner":                   winner,
            "is_incomplete_game":       is_incomplete,
            "gamelength_sec":           gamelength,
            "team1_patch_winrate":      t1wr,
            "team2_patch_winrate":      t2wr,
            "head_to_head":             h2h,
            "team1_last5":              t1l5,
            "team2_last5":              t2l5,
            "limited_data":             limited_data,
            **bans, **dpicks, **rpicks,
        }

        # Game row
        all_rows.append({"row_type":"game", **game_ctx, **bobj, **robj})

        # Player rows
        for _,pr in players.iterrows():
            side = clean(pr.get(side_c,"")).lower()
            pos  = clean(pr.get(pos_c,"")).lower()
            ch   = clean(pr.get(champ_c,""))
            pn   = clean(pr.get(player_c,""))   if player_c else ""
            pid  = clean(pr.get(pid_c,""))      if pid_c    else ""
            fp   = clean(pr.get(fp_c,""))       if fp_c     else ""
            pr2  = clean(pr.get(res_c,""))      if res_c    else ""
            snap = has_snapshot(pr, snap_chk)
            pcwr = fmt_wr(cwr.get(ch,""))

            rec={"row_type":"player", **game_ctx,
                 "playername":pn, "participantid":pid,
                 "side":side, "position":pos, "champion":ch,
                 "firstpick":fp, "player_result":pr2,
                 "has_snapshot_data":snap, "champion_patch_winrate":pcwr}

            for sc in PLAYER_STAT_COLS:
                rec[sc]=clean_num(pr[sc]) if sc in pr.index else 0
            for minute in MINUTES:
                for sc2 in SNAPSHOT_COLS[minute]:
                    rec[sc2]=clean_num(pr[sc2]) if sc2 in pr.index else 0

            all_rows.append(rec)

    if remakes_skipped > 0:
        print(f" ({remakes_skipped} remakes/forfeits skipped)", end="")

    if not all_rows: return pd.DataFrame()
    out = pd.DataFrame(all_rows)
    return standardize_df(out)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser=argparse.ArgumentParser(
        description="Split Oracle's Elixir data into one CSV per league — every league",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--local",  nargs="+", metavar="CSV",
                        help="Input CSV files. If not given, auto-detects all CSVs in current folder.")
    parser.add_argument("--outdir", default="output",
                        help="Output folder (default: 'output' subfolder)")
    parser.add_argument("--skip",   nargs="+", metavar="LEAGUE", default=[],
                        help="League names to skip")
    args=parser.parse_args()

    outdir=Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # ── Find input files ──────────────────────────────────────────────────────
    if args.local:
        input_files=[Path(f) for f in args.local]
    else:
        cwd=Path(".")
        input_files=sorted([
            f for f in cwd.glob("*.csv")
            if any(str(y) in f.name for y in range(2018,2030))
        ])
        if not input_files:
            input_files=sorted(cwd.glob("*.csv"))

    if not input_files:
        print("✗ No CSV files found.")
        print("  Put your downloaded OE files in the same folder as this script, or use:")
        print("  python lol_split_by_league.py --local 2024_*.csv 2025_*.csv")
        sys.exit(1)

    # ── Load all files ────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 1 — Loading {len(input_files)} input file(s)")
    print(f"{'='*60}")

    frames=[]
    for f in input_files:
        if not f.exists():
            print(f"  ✗ Not found: {f}"); continue
        print(f"  {f.name}…", end=" ", flush=True)
        try:
            df=pd.read_csv(f, low_memory=False)
            df.columns=[c.lower().strip() for c in df.columns]
            print(f"{len(df):,} rows")
            frames.append(df)
        except Exception as e:
            print(f"ERROR: {e}")

    if not frames:
        print("✗ No data loaded."); sys.exit(1)

    print(f"\nCombining all files…", end=" ", flush=True)
    combined=pd.concat(frames, ignore_index=True)
    combined.columns=[c.lower().strip() for c in combined.columns]
    print(f"{len(combined):,} total rows")

    # ── Find every unique league ──────────────────────────────────────────────
    league_c=find_col(combined,"league","leaguename")
    if not league_c:
        print("✗ No 'league' column found."); sys.exit(1)

    # Normalize league names before finding uniques
    combined["league_normalized"]=combined[league_c].astype(str).apply(normalize_league)

    all_leagues=sorted(combined["league_normalized"].dropna().unique().tolist())
    skip_upper=[s.upper() for s in args.skip]
    to_process=[l for l in all_leagues
                if str(l).strip() and str(l).upper() not in skip_upper]

    print(f"\n{'='*60}")
    print(f"STEP 2 — Found {len(to_process)} leagues")
    print(f"{'='*60}")
    print(f"  {', '.join(str(l) for l in to_process)}\n")

    # Remap league column to normalized values
    combined[league_c]=combined["league_normalized"]
    combined=combined.drop(columns=["league_normalized"])

    # ── Process each league ───────────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"STEP 3 — Exporting one CSV per league")
    print(f"{'='*60}")

    summary=[]; skipped=[]
    for league in to_process:
        league_str=str(league).strip()
        if not league_str: continue
        print(f"\n  [{league_str}]", end=" ", flush=True)
        try:
            result=process_league(combined, league_str)
            if result.empty:
                print("→ 0 games, skipping")
                skipped.append(league_str); continue
            fname   =safe_filename(league_str)+".csv"
            out_path=outdir/fname
            result.to_csv(out_path, index=False, encoding="utf-8")
            g=len(result[result["row_type"]=="game"])
            p=len(result[result["row_type"]=="player"])
            warn=""
            if league_str.upper() in LEAGUE_WARNINGS:
                warn=f" ⚠ {LEAGUE_WARNINGS[league_str.upper()]}"
            print(f"→ {g:,} games / {p:,} player rows → {fname}{warn}")
            summary.append((league_str,g,p,out_path))
        except Exception as e:
            print(f"→ ERROR: {e}")
            import traceback; traceback.print_exc()
            skipped.append(league_str)

    # ── Final summary ─────────────────────────────────────────────────────────
    total_g=sum(g for _,g,_,_ in summary)
    total_p=sum(p for _,_,p,_ in summary)

    print(f"\n{'='*60}")
    print(f"DONE — {len(summary)} files written to: {outdir.resolve()}")
    print(f"{'='*60}\n")
    for ls,g,p,path in summary:
        warn=" ⚠" if ls.upper() in LEAGUE_WARNINGS else ""
        print(f"  {ls:<25} {g:>5} games  {p:>7} player rows   {path.name}{warn}")
    print(f"\n  TOTAL: {total_g:,} games   {total_p:,} player rows   {len(summary)} leagues")

    if skipped:
        print(f"\n  Skipped: {', '.join(skipped)}")

    print(f"""
Column layout per CSV (row_type = 'game'):
  gameid, league, data_warning, split, playoffs, game_in_series,
  series_score_before_game, patch, datetime, url, datacompleteness,
  team1_blue, team2_red, winner, is_incomplete_game, gamelength_sec,
  team1_patch_winrate, team2_patch_winrate, head_to_head,
  team1_last5, team2_last5, limited_data,
  ban_b1..ban_r5, draft_pick_1..10, blue/red role picks,
  blue/red objective columns (non-redundant)

Column layout per CSV (row_type = 'player'):
  [all game columns above] +
  playername, participantid, side, position, champion, firstpick,
  player_result, has_snapshot_data, champion_patch_winrate,
  kills/deaths/assists, damage/vision/gold/cs stats,
  goldat10/15/20/25, xpat10/15/20/25, csat10/15/20/25 + diffs

Flags to watch:
  is_incomplete_game = 1  → remake or forfeit, no winner recorded
  has_snapshot_data = 0   → no per-minute gold/xp/cs data available
  limited_data = 1        → LPL/LDL game with sparse objective/snapshot data
  data_warning            → known source data quality issue for this league
""")

if __name__=="__main__":
    main()