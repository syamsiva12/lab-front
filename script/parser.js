/**
 * Minified by jsDelivr using Terser v5.19.2.
 * Original file: /npm/cron-parser@4.9.0/lib/parser.js
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
"use strict";var CronExpression=require("./expression");function CronParser(){}CronParser._parseEntry=function(r){var e=r.split(" ");if(6===e.length)return{interval:CronExpression.parse(r)};if(e.length>6)return{interval:CronExpression.parse(e.slice(0,6).join(" ")),command:e.slice(6,e.length)};throw new Error("Invalid entry: "+r)},CronParser.parseExpression=function(r,e){return CronExpression.parse(r,e)},CronParser.fieldsToExpression=function(r,e){return CronExpression.fieldsToExpression(r,e)},CronParser.parseString=function(r){for(var e=r.split("\n"),n={variables:{},expressions:[],errors:{}},s=0,i=e.length;s<i;s++){var o=null,t=e[s].trim();if(t.length>0){if(t.match(/^#/))continue;if(o=t.match(/^(.*)=(.*)$/))n.variables[o[1]]=o[2];else{var a=null;try{a=CronParser._parseEntry("0 "+t),n.expressions.push(a.interval)}catch(r){n.errors[t]=r}}}}return n},CronParser.parseFile=function(r,e){require("fs").readFile(r,(function(r,n){if(!r)return e(null,CronParser.parseString(n.toString()));e(r)}))},module.exports=CronParser;
//# sourceMappingURL=/sm/a1426d86cd12226589c3a0050bcbeaca29951a869f8d2822207dde556924cc76.map