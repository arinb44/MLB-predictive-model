import {drawRanked} from './gen-chart.mjs';
const hitters = [
  ["Aaron Judge","NYY",10.8],["Bobby Witt Jr.","KCR",9.4],["Shohei Ohtani","LAD",9.2],
  ["Juan Soto","NYY",7.9],["Gunnar Henderson","BAL",7.5],["Francisco Lindor","NYM",7.4],
  ["Jarren Duran","BOS",6.8],["Ketel Marte","ARI",6.5],["Elly De La Cruz","CIN",6.0],
  ["Jackson Merrill","SDP",5.3],["Marcus Semien","TEX",4.9],["Rafael Devers","BOS",4.6],
  ["Corbin Carroll","ARI",4.4],["José Ramírez","CLE",4.3],["William Contreras","MIL",4.2],
  ["Vladimir Guerrero Jr.","TOR",4.1],["Yordan Alvarez","HOU",4.0],["Mookie Betts","LAD",3.8],
].map(([name,team,v])=>({name,team,v}));
console.log(drawRanked(hitters,{metric:"WAR",fmt:v=>v.toFixed(1)}));
