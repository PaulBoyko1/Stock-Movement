/* Exploratory monthly allocation engine. Frozen E04-P1 remains a separate Python runner. */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.StockBacktest = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const defaults = Object.freeze({start:"2000-01",end:"2025-12",lookback:11,skip:1,
    topK:3,costBps:10,initialCapital:10000,rebalanceEvery:1});
  function monthNumber(value) {
    if (typeof value !== "string" || !/^\d{4}-(0[1-9]|1[0-2])$/.test(value))
      throw new Error("Use a valid YYYY-MM month.");
    const year=Number(value.slice(0,4));
    if (year<1900 || year>2200) throw new Error("Month outside supported calendar.");
    return year*12+Number(value.slice(5))-1;
  }
  function validateData(data) {
    if (!data || !Array.isArray(data.series) || !data.series.length || !Array.isArray(data.rows) || !data.rows.length)
      throw new Error("A monthly return panel and named series are required.");
    const ids=data.series.map(s=>s && s.id);
    if (ids.some(id=>typeof id!=="string"||!id.trim()) || new Set(ids).size!==ids.length)
      throw new Error("Series IDs must be nonempty and unique.");
    let previous=null;
    for (const row of data.rows) {
      const current=monthNumber(row.month);
      if (previous!==null && current!==previous+1) throw new Error("Duplicate, unordered or missing month in data.");
      if (!Array.isArray(row.returns) || row.returns.length!==ids.length ||
          row.returns.some(r=>typeof r!=="number" || !Number.isFinite(r) || r<=-1))
        throw new Error("Monthly returns must be finite decimal values above -100%, with one value per series.");
      previous=current;
    }
    return true;
  }
  function integer(value,min,max,label) {
    if (!Number.isInteger(value)||value<min||value>max) throw new Error(label+" must be an integer from "+min+" to "+max+".");
  }
  function summary(points, capital) {
    const n=points.length, mean=points.reduce((s,p)=>s+p.net,0)/n;
    const variance=points.reduce((s,p)=>s+(p.net-mean)**2,0)/(n-1);
    return {cagr:(points[n-1].wealth/capital)**(12/n)-1,volatility:Math.sqrt(variance*12),
      maxDrawdown:Math.min(0,...points.map(p=>p.drawdown)),finalWealth:points[n-1].wealth,
      turnover:points.reduce((s,p)=>s+p.turnover,0)*12/n};
  }
  function run(data, options={}) {
    validateData(data);
    const p={...defaults,...options};
    integer(p.lookback,1,60,"Formation months"); integer(p.skip,0,12,"Skipped months");
    integer(p.topK,1,data.series.length,"Holdings");
    if (typeof p.costBps!=="number"||!Number.isFinite(p.costBps)||p.costBps<0||p.costBps>100)
      throw new Error("Trading cost must be between 0 and 100 bp per dollar traded.");
    if (typeof p.initialCapital!=="number"||!Number.isFinite(p.initialCapital)||p.initialCapital<=0||p.initialCapital>1e12)
      throw new Error("Starting capital must be positive and no greater than one trillion.");
    if (![1,3].includes(p.rebalanceEvery)) throw new Error("Rebalance every 1 or 3 months.");
    if (monthNumber(p.start)>monthNumber(p.end)) throw new Error("Start must precede end.");
    const start=data.rows.findIndex(r=>r.month===p.start), end=data.rows.findIndex(r=>r.month===p.end);
    if (start<0||end<0) throw new Error("Selected dates are outside the available dataset.");
    if (start<p.lookback+p.skip) throw new Error("Insufficient history before the selected start for these formation and skipped months.");
    if (end-start+1<12) throw new Error("Choose at least 12 evaluation months.");
    const count=data.series.length, c=p.costBps/10000;
    function simulate(topK) {
      let weights=Array(count).fill(0), wealth=p.initialCapital, peak=wealth, selected=[];
      const points=[];
      for (let i=start;i<=end;i++) {
        const rebalance=(i-start)%p.rebalanceEvery===0;
        let target=weights.slice(), traded=0;
        if (rebalance) {
          const scores=data.series.map((_,j)=>{
            let value=1;
            for(let t=i-p.skip-p.lookback;t<i-p.skip;t++) value*=1+data.rows[t].returns[j];
            return value-1;
          });
          selected=Array.from({length:count},(_,j)=>j).sort((a,b)=>scores[b]-scores[a]||a-b).slice(0,topK);
          target=data.series.map((_,j)=>selected.includes(j)?1/topK:0);
          traded=target.reduce((s,w,j)=>s+Math.abs(w-weights[j]),0);
        }
        const gross=target.reduce((s,w,j)=>s+w*data.rows[i].returns[j],0);
        const terminal=i===end;
        const net=(1-c*traded)*(1+gross)*(terminal?1-c:1)-1;
        wealth*=1+net;
        if (!Number.isFinite(wealth)||wealth<=0) throw new Error("Nonpositive or nonfinite wealth; inspect returns and assumptions.");
        peak=Math.max(peak,wealth);
        points.push({net,wealth,drawdown:wealth/peak-1,turnover:traded+(terminal?1:0),
          selected:selected.map(j=>data.series[j].id),weights:target.slice(),rebalance,
          signalStart:rebalance?data.rows[i-p.skip-p.lookback].month:null,
          signalEnd:rebalance?data.rows[i-p.skip-1].month:null});
        weights=target.map((w,j)=>w*(1+data.rows[i].returns[j])/(1+gross));
      }
      return points;
    }
    const strategy=simulate(p.topK),benchmark=simulate(count);
    const points=strategy.map((s,i)=>({month:data.rows[start+i].month,
      strategyWealth:s.wealth,benchmarkWealth:benchmark[i].wealth,
      strategyReturn:s.net,benchmarkReturn:benchmark[i].net,
      strategyDrawdown:s.drawdown,benchmarkDrawdown:benchmark[i].drawdown,
      selected:s.selected.slice(),weights:s.weights.slice(),turnover:s.turnover,
      benchmarkTurnover:benchmark[i].turnover,rebalance:s.rebalance,
      signalStart:s.signalStart,signalEnd:s.signalEnd}));
    return {engineVersion:"monthly-explorer-1",points,months:points.length,params:{...p},
      metrics:{strategy:summary(strategy,p.initialCapital),benchmark:summary(benchmark,p.initialCapital)},
      datasetId:data.meta?.id||"unidentified",sourceSha256:data.meta?.sourceSha256||null,
      interpretation:"Exploratory retrospective monthly research portfolios; proportional allocation costs; not an executable ETF or stock forecast."};
  }
  return {run,validateData,defaults};
});
