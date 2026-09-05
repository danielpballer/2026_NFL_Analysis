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
    pure = json.load(open(C.OUTPUT / f"week{week}_{season}_pure_vs_blend.json"))
    narr = json.load(open(C.MANUAL / f"narratives_{season}_wk{week}.json"))["games"]
    NAMES = {"ARI":"Cardinals","ATL":"Falcons","BAL":"Ravens","BUF":"Bills","CAR":"Panthers","CHI":"Bears","CIN":"Bengals","CLE":"Browns","DAL":"Cowboys","DEN":"Broncos","DET":"Lions","GB":"Packers","HOU":"Texans","IND":"Colts","JAX":"Jaguars","KC":"Chiefs","LA":"Rams","LAC":"Chargers","LV":"Raiders","MIA":"Dolphins","MIN":"Vikings","NE":"Patriots","NO":"Saints","NYG":"Giants","NYJ":"Jets","PHI":"Eagles","PIT":"Steelers","SEA":"Seahawks","SF":"49ers","TB":"Buccaneers","TEN":"Titans","WAS":"Commanders"}
    def ml(x): x=int(x); return f"+{x}" if x>0 else str(x)
    def window(r):
        k=r['kickoff']
        if k.startswith('2026-09-09'): return ('Wednesday, Sept 9','Kickoff game')
        if k.startswith('2026-09-10'): return ('Thursday, Sept 10','Melbourne, neutral site')
        if k.startswith('2026-09-14'): return ('Monday, Sept 14','Monday Night Football')
        t=k.split(' ')[1]
        if t=='13:00': return ('Sunday, Sept 13','Early window, 1:00 ET')
        if t=='16:25': return ('Sunday, Sept 13','Late window, 4:25 ET')
        return ('Sunday, Sept 13','Sunday Night Football')
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
      <div class="kv"><span>2025 rating (pts vs avg, regressed)</span><span class="num">{r['home']} {r['home_rating_2025']:+.1f} · {r['away']} {r['away_rating_2025']:+.1f}</span></div>
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
