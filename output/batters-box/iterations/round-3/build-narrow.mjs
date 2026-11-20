import {drawRanked} from './gen-chart.mjs';
const mk=a=>a.map(([name,team,v])=>({name,team,v}));
const hitters = mk([["Aaron Judge","NYY",10.8],["Bobby Witt Jr.","KCR",9.4],["Shohei Ohtani","LAD",9.2],["Juan Soto","NYY",7.9],["Gunnar Henderson","BAL",7.5],["Francisco Lindor","NYM",7.4],["Jarren Duran","BOS",6.8],["Ketel Marte","ARI",6.5],["Elly De La Cruz","CIN",6.0],["Jackson Merrill","SDP",5.3],["Marcus Semien","TEX",4.9],["Rafael Devers","BOS",4.6],["Corbin Carroll","ARI",4.4],["José Ramírez","CLE",4.3],["William Contreras","MIL",4.2],["Vladimir Guerrero Jr.","TOR",4.1],["Yordan Alvarez","HOU",4.0],["Mookie Betts","LAD",3.8]]);
const teams = mk([["Yankees","NYY",116],["Dodgers","LAD",113],["Diamondbacks","ARI",111],["Orioles","BAL",109],["Padres","SDP",107],["Braves","ATL",104],["Guardians","CLE",103],["Royals","KCR",101],["Phillies","PHI",100],["Red Sox","BOS",99],["Astros","HOU",98],["Brewers","MIL",97],["Mets","NYM",96],["Cubs","CHC",94],["Tigers","DET",92]]);
const dh = mk([["Aaron Judge","NYY",10.8],["Juan Soto","NYY",7.9],["Anthony Volpe","NYY",3.1],["Austin Wells","NYY",2.6],["Gleyber Torres","NYY",2.1]]);
const dp = mk([["Gerrit Cole","NYY",3.4],["Carlos Rodón","NYY",3.1],["Luis Gil","NYY",2.8],["Clay Holmes","NYY",1.4],["Luke Weaver","NYY",1.3]]);
const W=327;
const out=[drawRanked(hitters,{W,metric:"WAR",fmt:v=>v.toFixed(1)}),
           drawRanked(teams,{W,metric:"Team OPS+",fmt:v=>v.toFixed(0),marker:"logo"}),
           drawRanked(dh,{W,metric:"WAR",fmt:v=>v.toFixed(1)}),
           drawRanked(dp,{W,metric:"WAR",fmt:v=>v.toFixed(1)})];
console.log(out.join("\n@@SPLIT@@\n"));
