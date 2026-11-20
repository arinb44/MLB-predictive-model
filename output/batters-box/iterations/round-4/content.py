MODEL = '''  <div class="sec-head">
    <h1>Model</h1>
    <p class="sec-note">What goes in, what comes out, and why the number tops out where it does.
      Every figure on this page is reproducible with <code>python scripts/evaluate.py</code>.</p>
  </div>

  <h2 class="sub">What goes in</h2>
  <div class="cells three">
    <div class="cell"><span class="tag">Team form</span><h3>Rolling windows</h3><p>Win percentage, run differential and runs scored over trailing windows &mdash; computed strictly from games before the one being predicted.</p></div>
    <div class="cell"><span class="tag">Rest</span><h3>Days and bullpen</h3><p>Days of rest, plus bullpen fatigue measured as extra innings absorbed in the trailing three days.</p></div>
    <div class="cell"><span class="tag">Park</span><h3>Trailing park factor</h3><p>Trailing park scoring average against the league average, estimated from this dataset rather than imported.</p></div>
    <div class="cell"><span class="tag">Pitcher</span><h3>Starter identity</h3><p>Starting-pitcher identity via Retrosheet (2015&ndash;2023), plus a trailing runs-allowed-in-own-starts proxy.</p></div>
    <div class="cell"><span class="tag">Elo</span><h3>Written from scratch</h3><p>An Elo rating that updates online after every game, so it needs no training split of its own.</p></div>
    <div class="cell"><span class="tag">Not used</span><h3>Platoon splits</h3><p>Starting-pitcher splits against opposing lineup handedness are not implemented. Neither is anything from during or after a game.</p></div>
  </div>

  <h2 class="sub">Three models, one problem</h2>
  <div class="prose">
    <p><strong>Logistic regression</strong> is the baseline. <strong>Gradient-boosted trees</strong> were expected to win on tabular data like this. The <strong>PyTorch</strong> model learns entity embeddings for team and starting-pitcher identity &mdash; thousands of distinct pitchers against thirty teams, the highest-cardinality input in the project &mdash; concatenated with the same numeric features under an MLP head, with a hand-written training loop.</p>
  </div>

  <h2 class="sub">Results</h2>
  <table class="rt">
    <caption>Walk-forward backtest, 2015&ndash;2024 &middot; 22,614 games &middot; trained models tested on 2018&ndash;2024 after a three-season burn-in</caption>
    <thead><tr><th>Model</th><th>Log-loss</th><th>Brier</th><th>Accuracy</th><th>n</th></tr></thead>
    <tbody>
      <tr><td>Elo (standalone)</td><td>0.6783</td><td>0.2427</td><td>56.97%</td><td>22,614</td></tr>
      <tr><td>Logistic regression</td><td>0.6759</td><td>0.2415</td><td class="best">57.81%</td><td>15,372</td></tr>
      <tr><td>XGBoost</td><td>0.6865</td><td>0.2464</td><td>56.41%</td><td>15,372</td></tr>
      <tr><td>PyTorch (entity embeddings)</td><td>0.6797</td><td>0.2433</td><td>57.17%</td><td>15,372</td></tr>
    </tbody>
  </table>

  <h2 class="sub">The ceiling is the point</h2>
  <div class="prose">
    <p>A realistic ceiling for MLB game prediction is about <strong>55&ndash;58% accuracy</strong>. Game-to-game variance in baseball is high, and a model claiming much better than that is almost certainly leaking information or overfitting. All four models land inside that band, which is a sanity check in itself: a leaky pipeline tends to show up as suspiciously <strong>good</strong> accuracy.</p>
    <p>What matters here is <strong>calibration</strong>, not raw accuracy. A model that says 60% should be right about 60% of the time across every prediction it makes at that number.</p>
  </div>

  <div class="callout">
    <p><strong>No leakage.</strong> Splits are chronological, never random k-fold, and every feature is a trailing window computed from games before the one being predicted &mdash; enforced by <code>tests/test_features.py</code>, not just claimed here.</p>
  </div>
'''

MATCHUPS = '''  <div class="sec-head">
    <h1>Matchups</h1>
    <p class="sec-note">Two teams, their season series, and every game between them &mdash; so the model&rsquo;s number sits next to what has actually happened.</p>
  </div>

  <div class="hh">
    <div class="pick">
      <div class="pick-head"><img width="40" height="40" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="Boston Red Sox logo" loading="lazy" onerror="this.style.visibility='hidden'"><span class="nm">Red Sox</span></div>
      <label for="hh-a">Team</label>
      <select id="hh-a"><option>Boston Red Sox</option></select>
      <p class="note">Away in 3 of 7 meetings</p>
    </div>
    <div class="mid">
      <span class="series-k">Season series</span>
      <span class="series">3&ndash;4</span>
      <span class="diff">Red Sox run differential +4</span>
      <span class="diff">Last meeting Aug 2</span>
    </div>
    <div class="pick">
      <div class="pick-head"><img width="40" height="40" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="Los Angeles Dodgers logo" loading="lazy" onerror="this.style.visibility='hidden'"><span class="nm">Dodgers</span></div>
      <label for="hh-b">Team</label>
      <select id="hh-b"><option>Los Angeles Dodgers</option></select>
      <p class="note">Home in 3 of 7 meetings</p>
    </div>
  </div>

  <h2 class="sub">Every meeting this season</h2>
  <div class="games">
    <div class="game"><span class="d">Aug 2</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>BOS at LAD</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">2&ndash;5</span><span class="w home">LAD</span></div>
    <div class="game"><span class="d">Aug 1</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>BOS at LAD</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">7&ndash;3</span><span class="w away">BOS</span></div>
    <div class="game"><span class="d">Jul 31</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>BOS at LAD</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">1&ndash;4</span><span class="w home">LAD</span></div>
    <div class="game"><span class="d">Jun 16</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>LAD at BOS</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">2&ndash;6</span><span class="w away">BOS</span></div>
    <div class="game"><span class="d">Jun 15</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>LAD at BOS</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">8&ndash;3</span><span class="w home">LAD</span></div>
    <div class="game"><span class="d">Jun 14</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>LAD at BOS</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">5&ndash;4</span><span class="w home">LAD</span></div>
    <div class="game"><span class="d">Jun 13</span><span class="fx"><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/119.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><span>LAD at BOS</span><img width="18" height="18" src="https://www.mlbstatic.com/team-logos/team-cap-on-dark/111.svg" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></span><span class="score">1&ndash;9</span><span class="w away">BOS</span></div>
  </div>

  <div class="callout">
    <p><strong>The series record is history, not a prediction.</strong> Head-to-head results are not a model input &mdash; seven games is far too small a sample to move a probability. The model sees these games only through each team&rsquo;s rolling form and Elo, exactly as it sees every other game.</p>
  </div>
'''

ABOUT = '''  <div class="sec-head">
    <h1>About the data</h1>
    <p class="sec-note">Where every number on this site comes from, and the line between what the model uses and what is here for context.</p>
  </div>

  <h2 class="sub">Sources</h2>
  <table class="rt">
    <thead><tr><th>Source</th><th>What it provides</th><th>Reaches the model</th></tr></thead>
    <tbody>
      <tr><td>MLB Stats API</td><td>Schedule, results, team totals, rosters, logos</td><td>Results and schedule</td></tr>
      <tr><td>Baseball-Reference</td><td>bWAR, OPS+, ERA+</td><td>No &mdash; display only</td></tr>
      <tr><td>Baseball Savant</td><td>wOBA, xwOBA, contact and plate-discipline rates</td><td>No &mdash; display only</td></tr>
      <tr><td>Retrosheet</td><td>Starting-pitcher identity, 2015&ndash;2023</td><td>Yes</td></tr>
      <tr><td>pybaseball</td><td>The client for the three above, 2015 onward</td><td>&mdash;</td></tr>
    </tbody>
  </table>

  <h2 class="sub">What the model actually sees</h2>
  <div class="cells">
    <div class="cell"><span class="tag">Model input</span><h3>Form, rest, park, pitcher, Elo</h3><p>Rolling team form, days of rest and bullpen fatigue, trailing park factors, starting-pitcher identity with a runs-allowed proxy, and an Elo rating.</p></div>
    <div class="cell"><span class="tag">Context only</span><h3>Every player stat on this site</h3><p>WAR, OPS+, ERA+, wOBA, xwOBA and the hitter lines beside a prediction are shown because they are interesting. None of them reach the model.</p></div>
  </div>

  <h2 class="sub">Caveats worth reading</h2>
  <div class="prose">
    <p><strong>Season to date.</strong> Player and team stats are current-season totals, so early in a season they move a lot on small samples.</p>
    <p><strong>Pitcher identity stops at 2023.</strong> Retrosheet coverage ends there, so later games fall back on the trailing performance proxy alone.</p>
    <p><strong>No platoon splits.</strong> Starting-pitcher performance against opposing lineup handedness is not modelled.</p>
    <p><strong>The host sleeps.</strong> On free-tier hosting the first request after about fifteen minutes idle takes 30&ndash;60 seconds to wake.</p>
  </div>
'''
