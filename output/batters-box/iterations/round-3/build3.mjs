import {drawRanked} from './gen-chart.mjs';
const h = [["Aaron Judge","NYY",10.8],["Juan Soto","NYY",7.9],["Anthony Volpe","NYY",3.1],["Austin Wells","NYY",2.6],["Gleyber Torres","NYY",2.1]].map(([name,team,v])=>({name,team,v}));
const p = [["Gerrit Cole","NYY",3.4],["Carlos Rodón","NYY",3.1],["Luis Gil","NYY",2.8],["Clay Holmes","NYY",1.4],["Luke Weaver","NYY",1.3]].map(([name,team,v])=>({name,team,v}));
console.log(drawRanked(h,{W:500,metric:"WAR",fmt:v=>v.toFixed(1)}));
console.log("@@SPLIT@@");
console.log(drawRanked(p,{W:500,metric:"WAR",fmt:v=>v.toFixed(1)}));
