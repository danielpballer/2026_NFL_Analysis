"""Stage 8 (web page): render output/week{week}_{season}_slate.html from the prediction outputs.

The page is a single self-contained HTML file. `fragment=True` returns the body content without the
document wrapper (what the claude.ai artifact publisher expects); the file written to output/ is a
complete standalone document that opens in any browser.
"""
from __future__ import annotations

import html
import json
import sys

from . import config as C

TEMPLATE = C.ROOT / "src" / "nflsim" / "templates" / "week1_page.html"


def build(season: int = C.SEASON, week: int = C.WEEK, fragment: bool = False) -> str:
    rows = json.load(open(C.OUTPUT / f"week{week}_{season}_predictions.json"))
    for r in rows:  # older outputs used the 2025-specific column names
        r.setdefault("home_rating_prior", r.get("home_rating_2025"))
        r.setdefault("away_rating_prior", r.get("away_rating_2025"))
    pure = json.load(open(C.OUTPUT / f"week{week}_{season}_pure_vs_blend.json"))
    npath = C.MANUAL / f"narratives_{season}_wk{week}.json"
    narr = json.load(open(npath))["games"] if npath.exists() else {}
    value = json.load(open(C.OUTPUT / f"week{week}_{season}_value.json"))
    NAMES = {"ARI":"Cardinals","ATL":"Falcons","BAL":"Ravens","BUF":"Bills","CAR":"Panthers","CHI":"Bears","CIN":"Bengals","CLE":"Browns","DAL":"Cowboys","DEN":"Broncos","DET":"Lions","GB":"Packers","HOU":"Texans","IND":"Colts","JAX":"Jaguars","KC":"Chiefs","LA":"Rams","LAC":"Chargers","LV":"Raiders","MIA":"Dolphins","MIN":"Vikings","NE":"Patriots","NO":"Saints","NYG":"Giants","NYJ":"Jets","PHI":"Eagles","PIT":"Steelers","SEA":"Seahawks","SF":"49ers","TB":"Buccaneers","TEN":"Titans","WAS":"Commanders"}
    def ml(x): x=int(x); return f"+{x}" if x>0 else str(x)
    import datetime as _d
    def window(r):
        day, t, _ = r['kickoff'].split(' ')
        d = _d.date.fromisoformat(day); label = d.strftime('%A, %b %-d')
        wd = d.weekday()
        if wd == 3: return (label, 'Thursday Night Football')
        if wd == 0: return (label, 'Monday Night Football')
        if wd != 6: return (label, 'Kickoff game')
        if t <= '13:30': return (label, 'Early window, 1:00 ET')
        if t <= '17:00': return (label, 'Late window, 4:05 and 4:25 ET')
        return (label, 'Sunday Night Football')
    groups={}
    for r in rows: groups.setdefault(window(r),[]).append(r)
    tier_cls={'Very High':'t-vhigh','High':'t-high','Moderate':'t-mod','Lean':'t-lean','Coin flip':'t-flip'}
    def esc(s): return html.escape(str(s)) if s is not None else ''
    def inj(d):
        if not d: return 'no material absences found'
        parts=[p.strip() for p in d.split(';')]
        parts=[p for p in parts if abs(float(p.rsplit('-',1)[1]))>=0.15]
        return esc('; '.join(parts)) if parts else 'only depth-chart absences'
    out=[]
    for (day,label),gs in groups.items():
        out.append(f'<section class="win"><header class="win-h"><h2>{day}</h2><span>{label}</span></header>')
        for r in gs:
            ph=r['p_home_win']; mk=r['market_p_home_devig']
            pick_home=r['predicted_winner']==r['home']
            p=r['win_probability']; tier=r['confidence']
            fair=r['fair_home_moneyline'] if pick_home else r['fair_away_moneyline']
            mkt=r['market_home_moneyline'] if pick_home else r['market_away_moneyline']
            edge=(ph-mk) if pick_home else (mk-ph)
            wx = 'indoor' if r['weather_note']=='indoor' else (f"{r['weather_note']}, {int(r['weather_temp_f'])}°F, wind {int(r['weather_wind_mph'])} mph, {int(r['weather_precip_pct'])}% precip ({r['weather_confidence']} confidence)" if r.get('weather_temp_f') is not None else r['weather_note'])
            hc=[t for t,f in ((r['home'],r['home_new_hc']),(r['away'],r['away_new_hc'])) if f]
            notes=[n for n in (r['home_qb_notes'],r['away_qb_notes']) if n]
            out.append(f'''
    <details class="game {tier_cls[tier]}">
     <summary>
      <div class="teams"><span class="tm {'pick' if not pick_home else ''}">{r['away']}<small>{NAMES[r['away']]}</small></span><span class="at">{'vs' if r['neutral_site'] else 'at'}</span><span class="tm {'pick' if pick_home else ''}">{r['home']}<small>{NAMES[r['home']]}</small></span></div>
      <div class="pickcol"><span class="pk">{r['predicted_winner']}</span><span class="tier">{tier}</span></div>
      <div class="meter" title="Model: {r['predicted_winner']} {p:.1%}. Market (vig removed): {r['predicted_winner']} {(mk if pick_home else 1-mk):.1%}."><span class="lbl l {'pick' if not pick_home else ''}">{r['away']} {1-ph:.0%}</span><div class="bar"><i class="fill {'r' if pick_home else ''}" style="width:{p*100:.1f}%"></i><b class="mid"></b><b class="mk" style="left:{(1-mk)*100:.1f}%"></b></div><span class="lbl r {'pick' if pick_home else ''}">{ph:.0%} {r['home']}</span></div>
      <div class="odds"><span class="num">{ml(fair)}</span><small>fair</small><span class="num dim">{ml(mkt)}</span><small>market</small></div>
      <div class="score num">{r['away']} {r['proj_away_pts']:.0f} · {r['home']} {r['proj_home_pts']:.0f}</div>
      <div class="edge num {'pos' if edge>0.02 else ('neg' if edge<-0.02 else '')}">{edge:+.1%}</div>
     </summary>
     <div class="why">
      <p class="story">{esc(narr.get(r['game_id'],''))}</p>
      <div class="kv"><span>Rating entering the week (pts vs avg)</span><span class="num">{r['home']} {r['home_rating_prior']:+.1f} · {r['away']} {r['away_rating_prior']:+.1f}</span></div>
      <div class="kv"><span>After QB, coaching, injury adjustments</span><span class="num">{r['home']} {r['home_rating_adj']:+.1f} · {r['away']} {r['away_rating_adj']:+.1f}</span></div>
      <div class="kv"><span>Quarterbacks</span><span>{r['home']} {esc(r['home_qb'])} <span class="num">({r['home_qb_adj']:+.1f})</span> · {r['away']} {esc(r['away_qb'])} <span class="num">({r['away_qb_adj']:+.1f})</span></span></div>
      <div class="kv"><span>{r['home']} injuries <span class="num">({r['home_injury_pts']:+.1f})</span></span><span>{inj(r['home_injury_details'])}</span></div>
      <div class="kv"><span>{r['away']} injuries <span class="num">({r['away_injury_pts']:+.1f})</span></span><span>{inj(r['away_injury_details'])}</span></div>
      {'<div class="kv"><span>New head coach</span><span>'+', '.join(hc)+' (rating regressed, variance widened)</span></div>' if hc else ''}
      <div class="kv"><span>Venue and weather</span><span>{esc(r['venue'])}, {esc(r['roof'])}; {esc(wx)}. Home edge <span class="num">{r['home_field_pts']:+.1f}</span></span></div>
      <div class="kv"><span>Margin, {r['home']} side</span><span class="num">model {r['model_margin_home']:+.1f} · market {r['market_spread_home']:+.1f} · blended {r['final_margin_home']:+.1f} · sd {r['margin_sd']:.1f}</span></div>
      <div class="kv"><span>Moneylines</span><span class="num">market {r['home']} {ml(r['market_home_moneyline'])} / {r['away']} {ml(r['market_away_moneyline'])} · model {r['home']} {ml(r['fair_home_moneyline'])} / {r['away']} {ml(r['fair_away_moneyline'])}</span></div>
      {''.join(f'<div class="kv note"><span>Note</span><span>{esc(n)}</span></div>' for n in notes)}
     </div>
    </details>''')
        out.append('</section>')
    tiers={}
    for r in rows: tiers[r['confidence']]=tiers.get(r['confidence'],0)+1
    tier_html=''.join(f'<span class="chip {tier_cls[t]}"><b>{tiers.get(t,0)}</b> {t}</span>' for t in ['High','Moderate','Lean','Coin flip'])
    page = TEMPLATE.read_text()
    WHY = {
     "2026_01_BAL_IND": "Indianapolis rated a little better than Baltimore in 2025, and the Ravens' rookie head coach and new offense cost them more than Lamar Jackson's return adds.",
     "2026_01_BUF_HOU": "Identical 2025 ratings, so Houston's home edge outweighs its offensive line and receiver losses; Buffalo also has a first-year head coach.",
     "2026_01_DAL_NYG": "The teams rated within half a point last year, and home field plus Jaxson Dart's year-two bump edges out Dallas on the data alone.",
    }
    flip_rows=[]; shifts=[]
    for r in rows:
        q=pure[r['game_id']]; ph=r['p_home_win']; pp=q['p_home_pure']; pm=q['p_home_market']
        def side(p): return (r['home'], p) if p>=.5 else (r['away'], 1-p)
        if q['flip']:
            (bt,bp),(pt,pq),(mt,mp)=side(ph),side(pp),side(pm)
            flip_rows.append(f"<tr><td>{r['away']} at {r['home']}</td><td><b>{bt}</b> {bp:.0%}</td><td><b>{pt}</b> {pq:.0%}</td><td><b>{mt}</b> {mp:.0%}</td><td>{WHY.get(r['game_id'],'')}</td></tr>")
        else:
            pk=r['predicted_winner']; bp=r['win_probability']; pq=pp if pk==r['home'] else 1-pp
            shifts.append((pq-bp, pk, bp, pq))
    shifts.sort(key=lambda x:-abs(x[0]))
    up=[f"{pk} {bp:.0%} to {pq:.0%}" for d,pk,bp,pq in shifts if d>0][:3]
    down=[f"{pk} {bp:.0%} to {pq:.0%}" for d,pk,bp,pq in shifts if d<0][:2]
    shift_text=(f"The other thirteen picks hold at any weighting, but their probabilities move. Pure data is more confident in {', '.join(up)}, and less confident in {', '.join(down)}, where the market's number is the main reason the favorite is priced so heavily.")
    vrows = []
    for l in value:
        if l["ev_per_dollar"] <= 0.02:
            continue
        mlt = f"+{l['market_ml']}" if l["market_ml"] > 0 else str(l["market_ml"])
        tag = "pick" if l["is_pick"] else "underdog"
        vrows.append(f"<tr><td>{l['side']} {mlt} ({l['matchup']})<span class='pickmark'>{tag}</span></td>"
                     f"<td class='num'>{l['model_p']:.0%}</td><td class='num'>{mlt}</td><td class='num'>{l['implied_p']:.0%}</td>"
                     f"<td class='num pos'>{l['ev_per_dollar']:+.0%}</td><td class='num'>{l['quarter_kelly']:.1%}</td></tr>")
    favs = [l for l in value if l["is_pick"] and l["model_p"] >= 0.7]
    fp = 1.0; fd = 1.0
    for l in favs:
        fp *= l["model_p"]; fd *= (1 + l["market_ml"] / 100) if l["market_ml"] > 0 else (1 + 100 / -l["market_ml"])
    value_note = (f"Everything not listed is negative expected value at the opening price, including most heavy favorites. "
                  f"A parlay of the {len(favs)} High-confidence picks ({', '.join(l['side'] for l in favs)}) hits about {fp:.0%} of the time and pays {fd-1:.1f} to 1, "
                  f"an expected return of {fp*fd-1:+.0%}: parlays multiply the book's margin and the model's error together. "
                  f"Prices here are the nflverse opening lines; compare with current odds before acting, because the largest edges come from injury news the opening line did not know about.")
    # track record from every evaluated week plus the pre-season backtest
    track = []
    bt = C.OUTPUT / "backtest_2025_wk1_scores.csv"
    labels = {"p_blend": "Model + market blend", "blend": "Model + market blend", "p_model": "Model only", "pure_model": "Model only",
              "p_market_spread": "Market spread only", "market_spread": "Market spread only", "p_market_ml": "Market moneyline only", "market_ml": "Market moneyline only"}
    import csv
    if bt.exists():
        for r in csv.DictReader(open(bt)):
            if r["method"] in labels:
                track.append(f"<tr><td>2025 wk 1 (backtest)</td><td>{labels[r['method']]}</td><td class='num'>{float(r['log_loss']):.3f}</td><td class='num'>{float(r['brier']):.3f}</td><td class='num'>{round(float(r['accuracy'])*16)} / 16</td></tr>")
    for w in range(1, week):
        f = C.OUTPUT / f"week{w}_{season}_evaluation_scores.csv"
        if f.exists():
            for r in csv.DictReader(open(f)):
                if r["method"] in labels:
                    track.append(f"<tr><td>{season} wk {w}</td><td>{labels[r['method']]}</td><td class='num'>{float(r['log_loss']):.3f}</td><td class='num'>{float(r['brier']):.3f}</td><td class='num'>{round(float(r['accuracy'])*16)} / 16</td></tr>")
    changes_path = C.MANUAL / f"model_changes_{season}_wk{week}.html"
    changes = changes_path.read_text() if changes_path.exists() else ""
    nflips = sum(1 for r in rows if pure[r['game_id']]['flip'])
    flip_intro = (f"Run the data alone and {nflips} pick{'s' if nflips != 1 else ''} flip{'' if nflips != 1 else 's'}." if nflips else "Run the data alone and no pick flips; the market only moves the probabilities.")
    import datetime as _dt
    page = page.replace('{{VALUE}}', ''.join(vrows)).replace('{{VALUE_NOTE}}', value_note)
    page = page.replace('{{WEEK}}', str(week)).replace('{{NGAMES}}', str(len(rows))).replace('{{BUILT}}', f"built {_dt.date.today().strftime('%b %-d, %Y')}")
    page = page.replace('{{TRACK}}', ''.join(track)).replace('{{CHANGES}}', changes).replace('{{FLIP_INTRO}}', flip_intro)
    page = page.replace('{{GAMES}}',''.join(out)).replace('{{TIERS}}',tier_html).replace('{{FLIPS}}',''.join(flip_rows)).replace('{{SHIFTS}}',shift_text)
    if fragment:
        return page
    title_line, _, rest = page.partition("\n")   # template starts with the <title> tag
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            + title_line.strip() + "\n<style>[hidden]{display:none!important}</style>\n</head>\n<body>\n" + rest + "\n</body>\n</html>\n")


def main():
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    out = C.OUTPUT / f"week{C.WEEK}_{C.SEASON}_slate.html"
    out.write_text(build())
    print(f"wrote {out}")
    if "--fragment" in sys.argv:
        frag = C.OUTPUT / f"week{C.WEEK}_{C.SEASON}_slate_fragment.html"
        frag.write_text(build(fragment=True))
        print(f"wrote {frag}")


if __name__ == "__main__":
    main()
