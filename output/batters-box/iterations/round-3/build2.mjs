import {drawRanked} from './gen-chart.mjs';
const teams = [
  ["Yankees","NYY",116],["Dodgers","LAD",113],["Diamondbacks","ARI",111],["Orioles","BAL",109],
  ["Padres","SDP",107],["Braves","ATL",104],["Guardians","CLE",103],["Royals","KCR",101],
  ["Phillies","PHI",100],["Red Sox","BOS",99],["Astros","HOU",98],["Brewers","MIL",97],
  ["Mets","NYM",96],["Cubs","CHC",94],["Tigers","DET",92],
].map(([name,team,v])=>({name,team,v}));
console.log(drawRanked(teams,{metric:"Team OPS+",fmt:v=>v.toFixed(0),marker:"logo"}));
