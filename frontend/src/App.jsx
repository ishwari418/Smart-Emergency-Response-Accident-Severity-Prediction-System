import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, BarChart3, CarFront, Check, ChevronLeft, ChevronRight,
  CircleHelp, Clock3, Database, Download, FileChartColumn, FileUp, Gauge,
  LayoutDashboard, Menu, RotateCcw, ShieldAlert, Sparkles, TableProperties,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api, errorMessage } from "./services/api.js";

const navigation = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "prediction", label: "Severity Prediction", icon: ShieldAlert },
  { id: "analytics", label: "Accident Analytics", icon: BarChart3 },
  { id: "evaluation", label: "Model Evaluation", icon: Gauge },
  { id: "batch", label: "Batch Prediction", icon: FileUp },
  { id: "data", label: "Data Management", icon: Database },
  { id: "about", label: "About Project", icon: CircleHelp },
];

const severityColors = ["#d5544d", "#e79a46", "#e5bd4a", "#35a889"];
const chartColors = ["#16967a", "#4d9fbd", "#e3a34e", "#9674bd", "#d66565"];
const categories = {
  road_type: ["Single carriageway", "Dual carriageway", "Roundabout", "One-way street", "Slip road"],
  weather_conditions: ["Fine", "Rain", "Snow", "Fog", "Windy"],
  road_surface: ["Dry", "Wet", "Icy", "Snow-covered"],
  light_conditions: ["Daylight", "Darkness - lit", "Darkness - unlit", "Dawn or dusk"],
  traffic_density: ["Low", "Medium", "High"],
  junction_type: ["Not at junction", "T-junction", "Crossroads", "Roundabout", "Private drive"],
  urban_or_rural: ["Urban", "Rural"],
  vehicle_type: ["Car", "Motorcycle", "Truck", "Bus", "Van"],
  day_of_week: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
};
const defaults = {
  number_of_vehicles: 2,
  number_of_casualties: 1,
  speed_limit: 40,
  road_type: "Single carriageway",
  weather_conditions: "Fine",
  road_surface: "Dry",
  light_conditions: "Daylight",
  traffic_density: "Medium",
  junction_type: "T-junction",
  urban_or_rural: "Urban",
  driver_age: 35,
  vehicle_type: "Car",
  visibility_km: 15,
  hour: 14,
  day_of_week: "Wednesday",
};
const numericInputs = [
  ["number_of_vehicles", "Vehicles involved", 1, 10],
  ["number_of_casualties", "Casualties", 0, 20],
  ["speed_limit", "Speed limit (mph)", 20, 70],
  ["driver_age", "Driver age", 16, 100],
  ["visibility_km", "Visibility (km)", 0.1, 20],
  ["hour", "Accident hour (0-23)", 0, 23],
];

function paramsFrom(filters) {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ""));
}

function PageHeading({ title, description, actions }) {
  return (
    <div className="page-heading">
      <div><h1>{title}</h1><p>{description}</p></div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

function Panel({ title, hint, children, className = "" }) {
  return <section className={`panel ${className}`}>
    <div className="panel-title">{title}</div>
    {hint && <div className="panel-hint">{hint}</div>}
    {children}
  </section>;
}

function ChartPanel({ title, hint, data, kind = "bar", color = chartColors[0], height = 245 }) {
  const chartData = data || [];
  return <Panel title={title} hint={hint}>
    {chartData.length === 0 ? <div className="empty-state">No records match the selected filters.</div> :
      <div className="chart-wrap" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {kind === "pie" ? (
            <PieChart>
              <Tooltip formatter={(value) => [Number(value).toLocaleString(), "Accidents"]} />
              <Legend verticalAlign="bottom" height={28} iconType="circle" wrapperStyle={{ fontSize: 10 }} />
              <Pie data={chartData} dataKey="count" nameKey="name" innerRadius={56} outerRadius={86} paddingAngle={3}>
                {chartData.map((item, index) => <Cell key={item.name} fill={severityColors[index % severityColors.length]} />)}
              </Pie>
            </PieChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 5, right: 12, left: -14, bottom: 20 }}>
              <CartesianGrid stroke="#eef2f4" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#82929b" }} angle={chartData.length > 7 ? -25 : 0} textAnchor={chartData.length > 7 ? "end" : "middle"} interval={0} />
              <YAxis tick={{ fontSize: 9, fill: "#82929b" }} />
              <Tooltip formatter={(value) => [Number(value).toLocaleString(), "Accidents"]} />
              <Bar dataKey="count" fill={color} radius={[4, 4, 0, 0]} maxBarSize={38} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    }
  </Panel>;
}

function StatCard({ title, value, note, icon: Icon }) {
  return <div className="stat-card">
    <div className="stat-label">{title}<span className="stat-icon"><Icon size={16} /></span></div>
    <div className="stat-value">{value}</div>
    <div className="stat-foot">{note}</div>
  </div>;
}

function TextError({ children }) {
  return children ? <div className="error-box" role="alert">{children}</div> : null;
}

function LoadingPanel({ text = "Loading data…" }) {
  return <div className="panel empty-state"><Activity size={17} className="mx-auto mb-2 animate-pulse" />{text}</div>;
}

function Filters({ value, onChange, includeDate = false }) {
  function set(key, next) { onChange({ ...value, [key]: next }); }
  return <div className="control-row">
    <div className="field"><label>Severity</label><select value={value.severity || ""} onChange={(event) => set("severity", event.target.value)}>
      <option value="">All severities</option><option value="1">Fatal</option><option value="2">Serious Injury</option><option value="3">Minor Injury</option><option value="4">Property Damage Only</option>
    </select></div>
    <div className="field"><label>Weather</label><select value={value.weather || ""} onChange={(event) => set("weather", event.target.value)}>
      <option value="">All weather</option>{categories.weather_conditions.map((item) => <option key={item}>{item}</option>)}
    </select></div>
    <div className="field"><label>Road type</label><select value={value.road_type || ""} onChange={(event) => set("road_type", event.target.value)}>
      <option value="">All road types</option>{categories.road_type.map((item) => <option key={item}>{item}</option>)}
    </select></div>
    {includeDate && <>
      <div className="field"><label>From date</label><input type="date" value={value.date_from || ""} onChange={(event) => set("date_from", event.target.value)} /></div>
      <div className="field"><label>To date</label><input type="date" value={value.date_to || ""} onChange={(event) => set("date_to", event.target.value)} /></div>
    </>}
    <button className="btn btn-secondary" type="button" onClick={() => onChange({})}><RotateCcw size={14} />Clear</button>
  </div>;
}

function DashboardPage({ data, loading, filters, setFilters, error }) {
  const params = paramsFrom(filters);
  return <>
    <PageHeading title="Accident overview" description="Explore patterns across the generated accident records." actions={<>
      <a className="btn btn-secondary" href={api.exportUrl(params)}><Download size={14} />Export CSV</a>
      <a className="btn btn-secondary" href={api.reportUrl(params)}><FileChartColumn size={14} />PDF report</a>
    </>} />
    <Filters value={filters} onChange={setFilters} includeDate />
    <TextError>{error}</TextError>
    {loading || !data ? <LoadingPanel /> : <>
      <div className="stat-grid">
        <StatCard title="Accident records" value={Number(data.total_accidents).toLocaleString()} note="Records in current view" icon={CarFront} />
        <StatCard title="Recorded casualties" value={Number(data.total_casualties).toLocaleString()} note="Across filtered records" icon={Activity} />
        <StatCard title="Avg. vehicles" value={Number(data.average_vehicles).toFixed(2)} note="Vehicles per accident" icon={Gauge} />
        <StatCard title="Most common severity" value={data.most_frequent_severity || "—"} note="Highest record count" icon={ShieldAlert} />
      </div>
      <div className="notice mb-4"><Sparkles size={16} className="mt-0.5 shrink-0" /><span>These records are synthetic and generated for educational demonstration; they are not official historical accident data. Charts show associations, not causes.</span></div>
      <div className="chart-grid">
        <ChartPanel title="Accidents by severity" hint="Severity labels: 1 Fatal · 2 Serious Injury · 3 Minor Injury · 4 Property Damage Only" data={data.severity} kind="pie" />
        <ChartPanel title="Accidents by weekday" hint="Counts grouped by day of the week" data={data.by_day} color="#5597bb" />
        <ChartPanel title="Accidents by hour" hint="Hour is recorded in 24-hour format" data={data.by_hour} color="#e2a04b" />
        <ChartPanel title="Weather conditions" hint="Reported weather categories" data={data.by_weather} color="#6b8ebd" />
        <ChartPanel title="Road type" hint="Records grouped by road classification" data={data.by_road_type} color="#9279b7" />
        <ChartPanel title="Light conditions" hint="Daylight, darkness, and dawn/dusk" data={data.by_light} color="#d8796c" />
      </div>
    </>}
  </>;
}

function PredictionPage() {
  const [values, setValues] = useState(defaults);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  function change(key, value) { setValues((current) => ({ ...current, [key]: value })); }
  async function submit(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    setBusy(true);
    const body = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, numericInputs.some(([field]) => field === key) ? Number(value) : value]));
    try { setResult(await api.predict(body)); }
    catch (requestError) { setError(errorMessage(requestError)); }
    finally { setBusy(false); }
  }
  return <>
    <PageHeading title="Severity prediction" description="Estimate a severity category from road, vehicle, and environmental conditions." />
    <Panel title="Accident conditions" hint="Enter values for every field. The model was trained using the same feature names and categories.">
      <TextError>{error}</TextError>
      <form onSubmit={submit}>
        <div className="form-grid">
          {numericInputs.map(([key, label, min, max]) => <div className="field" key={key}>
            <label htmlFor={`feature-${key}`}>{label}</label>
            <input id={`feature-${key}`} type="number" min={min} max={max} step={key === "visibility_km" ? "0.1" : "1"} required value={values[key]} onChange={(event) => change(key, event.target.value)} />
          </div>)}
          {Object.entries(categories).map(([key, choices]) => <div className="field" key={key}>
            <label htmlFor={`feature-${key}`}>{key.replaceAll("_", " ")}</label>
            <select id={`feature-${key}`} value={values[key]} onChange={(event) => change(key, event.target.value)}>
              {choices.map((choice) => <option key={choice}>{choice}</option>)}
            </select>
          </div>)}
        </div>
        <button className="btn mt-5" type="submit" disabled={busy}>{busy ? "Predicting…" : <><ShieldAlert size={15} />Predict Severity</>}</button>
      </form>
    </Panel>
    {result && <div className="result-card">
      <div className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Predicted category</div>
      <div className="result-name">{result.severity_label}</div>
      <div className="panel-hint mt-1">Prediction is based on the saved trained pipeline.</div>
      <div className="chart-wrap mt-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={result.probabilities} layout="vertical" margin={{ left: 18, right: 20 }}>
            <CartesianGrid stroke="#e5eeea" horizontal={false} />
            <XAxis type="number" domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={{ fontSize: 10 }} />
            <YAxis type="category" dataKey="label" width={142} tick={{ fontSize: 10 }} />
            <Tooltip formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, "Probability"]} />
            <Bar dataKey="probability" fill="#168d75" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="notice mt-3"><AlertTriangle size={15} className="mt-0.5 shrink-0" /><span>{result.disclaimer} This educational prototype does not dispatch emergency services or guarantee real-world outcomes.</span></div>
    </div>}
  </>;
}

function AnalyticsPage({ filters, setFilters }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const filterKey = JSON.stringify(filters);
  useEffect(() => {
    let active = true;
    setLoading(true);
    api.analytics({ ...paramsFrom(filters), search, page }).then((result) => {
      if (active) { setData(result); setError(""); }
    }).catch((requestError) => { if (active) setError(errorMessage(requestError)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filterKey, search, page]);
  function updateFilters(next) { setFilters(next); setPage(1); }
  const totalPages = Math.max(1, Math.ceil((data?.total_records || 0) / (data?.page_size || 25)));
  return <>
    <PageHeading title="Accident analytics" description="Compare severity, conditions, and road patterns. These summaries describe associations and do not prove causation." actions={<a className="btn btn-secondary" href={api.exportUrl({ ...paramsFrom(filters), search })}><Download size={14} />Download filtered CSV</a>} />
    <Filters value={filters} onChange={updateFilters} />
    <div className="control-row">
      <div className="field"><label>Search records</label><input placeholder="Search any field…" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} /></div>
    </div>
    <TextError>{error}</TextError>
    {loading && !data ? <LoadingPanel /> : data && <>
      <div className="stat-grid">
        <StatCard title="Matching records" value={Number(data.total_records).toLocaleString()} note="After applied filters and search" icon={TableProperties} />
        <StatCard title="Casualties" value={Number(data.casualty_total).toLocaleString()} note="Recorded for matching records" icon={Activity} />
        <StatCard title="Severity categories" value={data.severity.length} note="Labels represented in this view" icon={ShieldAlert} />
        <StatCard title="Current page" value={`${page} / ${totalPages}`} note="25 records per page" icon={Database} />
      </div>
      <div className="chart-grid">
        <ChartPanel title="Severity distribution" data={data.severity} kind="pie" />
        <ChartPanel title="Weather-wise records" data={data.by_weather} color="#5597bb" />
        <ChartPanel title="Road types" data={data.by_road_type} color="#9279b7" />
        <ChartPanel title="Accidents by hour" data={data.by_hour} color="#e2a04b" />
        <ChartPanel title="Accidents by weekday" data={data.by_day} color="#16967a" />
        <ChartPanel title="Urban and rural" data={data.by_area} color="#d8796c" />
        <ChartPanel title="Vehicle types" data={data.by_vehicle} color="#668cc0" />
      </div>
      <Panel title="Accident records" hint="Search and filter the synthetic dataset.">
        <div className="table-wrap">
          <table><thead><tr>{["ID", "Date", "Severity", "Vehicles", "Casualties", "Weather", "Road type", "Area"].map((heading) => <th key={heading}>{heading}</th>)}</tr></thead>
            <tbody>{data.records.map((record) => <tr key={record.accident_id}>
              <td>{record.accident_id}</td><td>{record.date}</td><td>{record.severity} · {["", "Fatal", "Serious Injury", "Minor Injury", "Property Damage Only"][record.severity]}</td>
              <td>{record.number_of_vehicles}</td><td>{record.number_of_casualties}</td><td>{record.weather_conditions}</td><td>{record.road_type}</td><td>{record.urban_or_rural}</td>
            </tr>)}</tbody>
          </table>
          {data.records.length === 0 && <div className="empty-state">No records match this search.</div>}
        </div>
        <div className="pagination">
          <span>Showing {data.records.length ? (page - 1) * data.page_size + 1 : 0}–{Math.min(page * data.page_size, data.total_records)} of {Number(data.total_records).toLocaleString()} records</span>
          <div className="flex gap-2">
            <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronLeft size={14} />Previous</button>
            <button className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>Next<ChevronRight size={14} /></button>
          </div>
        </div>
      </Panel>
    </>}
  </>;
}

function EvaluationPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.metrics().then(setMetrics).catch((requestError) => setError(errorMessage(requestError))).finally(() => setLoading(false));
  }, []);
  if (loading) return <><PageHeading title="Model evaluation" description="Held-out test metrics from the saved model training run." /><LoadingPanel /></>;
  return <>
    <PageHeading title="Model evaluation" description="Evaluation is computed from a stratified held-out test split. No metrics are hardcoded." />
    <TextError>{error}</TextError>
    {!metrics ? <div className="panel empty-state">Generate the dataset and train the model from the backend folder, then refresh this page.<p className="mt-2 font-mono text-[11px]">python generate_dataset.py<br />python train_model.py</p></div> : <>
      <div className="notice"><Check size={15} className="mt-0.5 shrink-0" /><span>{metrics.model_name} · {Number(metrics.training_records).toLocaleString()} training records · {Number(metrics.test_records).toLocaleString()} test records. The test set was not used to fit the model.</span></div>
      <div className="metric-grid">
        {[["Accuracy", metrics.accuracy], ["Macro precision", metrics.macro_precision], ["Macro recall", metrics.macro_recall], ["Macro F1-score", metrics.macro_f1], ["Weighted F1-score", metrics.weighted_f1]].map(([label, value]) =>
          <div className="metric-box" key={label}><span>{label}</span><strong>{Number(value).toFixed(3)}</strong></div>)}
      </div>
      <div className="chart-grid">
        <Panel title="Confusion matrix" hint="Rows are actual classes; columns are predicted classes.">
          <div className="table-wrap"><table className="heatmap"><thead><tr><th>Actual \ Predicted</th>{metrics.labels_order.map((label) => <th key={label}>{label}: {metrics.class_labels[label]}</th>)}</tr></thead>
            <tbody>{metrics.confusion_matrix.map((row, rowIndex) => <tr key={rowIndex}><th>{metrics.labels_order[rowIndex]}: {metrics.class_labels[metrics.labels_order[rowIndex]]}</th>
              {row.map((count, columnIndex) => {
                const peak = Math.max(...metrics.confusion_matrix.flat());
                return <td key={columnIndex} style={{ backgroundColor: `rgba(22, 141, 117, ${peak ? 0.08 + 0.75 * count / peak : 0.08})`, color: count > peak * 0.45 ? "white" : "#274c5b" }}>{Number(count).toLocaleString()}</td>;
              })}
            </tr>)}</tbody></table></div>
        </Panel>
        <Panel title="Per-class scores" hint="Precision, recall, F1-score, and test support">
          <div className="table-wrap"><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead>
            <tbody>{Object.entries(metrics.classification_report).map(([label, scores]) => <tr key={label}><td>{label}</td><td>{scores.precision.toFixed(3)}</td><td>{scores.recall.toFixed(3)}</td><td>{scores["f1-score"].toFixed(3)}</td><td>{Number(scores.support).toLocaleString()}</td></tr>)}</tbody>
          </table></div>
        </Panel>
      </div>
      <Panel title="Reading the metrics">
        <div className="about-grid"><p className="text-xs leading-6 text-slate-600"><b>Accuracy</b> is the fraction of all test records classified correctly. <b>Precision</b> reflects how often a predicted class was correct; <b>recall</b> reflects how many actual records of a class were found. <b>F1</b> balances precision and recall. Macro scores weight each class equally.</p>
          <p className="text-xs leading-6 text-slate-600">Scores measure performance on this synthetic dataset only. They are not evidence of real-world emergency performance, and the model should not be used for operational decisions.</p></div>
      </Panel>
    </>}
  </>;
}

function toCsv(columns, rows) {
  const quote = (value) => {
    const text = value == null ? "" : String(value);
    return `"${text.replaceAll('"', '""')}"`;
  };
  return [columns.map(quote).join(","), ...rows.map((row) => columns.map((column) => quote(row[column])).join(","))].join("\r\n");
}

function BatchPage() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    if (!file) { setError("Choose a CSV file first."); return; }
    if (file.size > 10 * 1024 * 1024) { setError("File exceeds the 10 MB upload limit."); return; }
    if (!file.name.toLowerCase().endsWith(".csv")) { setError("Select a .csv file."); return; }
    setBusy(true); setError(""); setResult(null);
    try { setResult(await api.batchPredict(file)); }
    catch (requestError) { setError(errorMessage(requestError)); }
    finally { setBusy(false); }
  }
  function download() {
    const blob = new Blob([toCsv(result.columns, result.records)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = "batch-predictions.csv"; anchor.click();
    URL.revokeObjectURL(url);
  }
  return <>
    <PageHeading title="Batch prediction" description="Upload up to 5,000 feature rows in a CSV file. The severity target column is not required." />
    <Panel title="Upload feature CSV" hint="Required input feature columns match the single-prediction form. Maximum file size 10 MB.">
      <div className="notice mb-3"><FileUp size={15} className="mt-0.5 shrink-0" /><span>Required columns: {["number_of_vehicles", "number_of_casualties", "speed_limit", "road_type", "weather_conditions", "road_surface", "light_conditions", "traffic_density", "junction_type", "urban_or_rural", "driver_age", "vehicle_type", "visibility_km", "hour", "day_of_week"].join(", ")}.</span></div>
      <TextError>{error}</TextError>
      <form className="control-row" onSubmit={submit}>
        <div className="field"><label htmlFor="batch-file">CSV file</label><input id="batch-file" type="file" accept=".csv,text/csv" onChange={(event) => { setFile(event.target.files?.[0] || null); setError(""); }} /></div>
        <button className="btn" type="submit" disabled={busy}>{busy ? "Predicting rows…" : "Run batch prediction"}</button>
      </form>
    </Panel>
    {result && <Panel className="mt-4" title={`${Number(result.row_count).toLocaleString()} predictions completed`} hint="Preview includes the original uploaded columns and prediction probabilities." >
      <div className="flex justify-end mb-3"><button className="btn btn-secondary" onClick={download}><Download size={14} />Download prediction CSV</button></div>
      <div className="table-wrap"><table><thead><tr>{result.columns.slice(0, 9).map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr></thead>
        <tbody>{result.records.slice(0, 20).map((record, index) => <tr key={index}>{result.columns.slice(0, 9).map((column) => <td key={column}>{String(record[column] ?? "")}</td>)}</tr>)}</tbody>
      </table></div>
      {result.row_count > 20 && <div className="panel-hint mt-3">Showing first 20 rows; the CSV download contains all {result.row_count.toLocaleString()} returned rows.</div>}
    </Panel>}
  </>;
}

function DataPage() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const refresh = () => {
    setLoading(true);
    api.dataSummary().then((data) => { setSummary(data); setError(""); }).catch((requestError) => setError(errorMessage(requestError))).finally(() => setLoading(false));
  };
  useEffect(() => { refresh(); }, []);
  async function regenerate() {
    const confirmed = window.confirm("Regenerate and replace the current dataset? A timestamped CSV backup will be created. Existing model artifacts will also be backed up and removed; retraining will be required.");
    if (!confirmed) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await api.regenerate();
      setMessage(`${result.message} Backup: ${result.dataset_backup || "none"}`);
      refresh();
    } catch (requestError) { setError(errorMessage(requestError)); }
    finally { setBusy(false); }
  }
  return <>
    <PageHeading title="Data management" description="Inspect the locally generated dataset, its quality summary, and a sample of records." actions={<a className="btn btn-secondary" href={api.datasetUrl}><Download size={14} />Download dataset</a>} />
    <TextError>{error}</TextError>
    {message && <div className="success-box">{message}</div>}
    {loading && !summary ? <LoadingPanel /> : summary && <>
      <div className="stat-grid">
        <StatCard title="Dataset records" value={Number(summary.rows).toLocaleString()} note="Rows in the current CSV" icon={TableProperties} />
        <StatCard title="Columns" value={summary.columns} note="Including identifiers and target" icon={Database} />
        <StatCard title="Duplicate rows" value={summary.duplicate_rows} note="Exact duplicate records" icon={RotateCcw} />
        <StatCard title="Missing values" value={Object.values(summary.missing_values).reduce((sum, value) => sum + value, 0)} note="Total null cells" icon={AlertTriangle} />
      </div>
      <div className="chart-grid">
        <Panel title="Severity distribution" hint="Synthetic severity labels and record counts">
          <div className="table-wrap"><table><thead><tr><th>Severity</th><th>Records</th></tr></thead><tbody>{summary.severity_distribution.map((item) => <tr key={item.name}><td>{item.name}</td><td>{Number(item.count).toLocaleString()}</td></tr>)}</tbody></table></div>
        </Panel>
        <Panel title="Available columns" hint="Columns in the accident dataset">
          <div className="flex flex-wrap gap-2">{summary.column_names.map((column) => <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] text-slate-600" key={column}>{column}</span>)}</div>
        </Panel>
        <Panel className="wide" title="Missing-value counts" hint="A zero count means the column has no missing values.">
          <div className="table-wrap"><table><thead><tr>{Object.keys(summary.missing_values).map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr></thead><tbody><tr>{Object.values(summary.missing_values).map((count, index) => <td key={index}>{Number(count).toLocaleString()}</td>)}</tr></tbody></table></div>
        </Panel>
        <Panel className="wide" title="Dataset sample" hint="First 10 records">
          <div className="table-wrap"><table><thead><tr>{summary.column_names.slice(0, 9).map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr></thead>
            <tbody>{summary.sample.map((row) => <tr key={row.accident_id}>{summary.column_names.slice(0, 9).map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}</tr>)}</tbody>
          </table></div>
        </Panel>
      </div>
      <Panel title="Regenerate synthetic demo data" hint="Creates a timestamped backup of the current CSV. Any existing model and metrics artifacts are backed up and removed because they would no longer match.">
        <button className="btn btn-danger" disabled={busy} onClick={regenerate}><RotateCcw size={14} />{busy ? "Regenerating…" : "Regenerate dataset"}</button>
      </Panel>
    </>}
  </>;
}

function AboutPage() {
  return <>
    <PageHeading title="About this project" description="A student-built, educational prototype for learning about accident data, classification, and analytics." />
    <div className="about-grid">
      <Panel title="Project overview"><p className="text-xs leading-6 text-slate-600">Roadwise explores a machine-learning workflow that estimates a severity category from road, vehicle, and environmental conditions. The dataset is generated locally and deterministically to make the project runnable without paid services, external APIs, or manual data entry.</p></Panel>
      <Panel title="Technology stack"><ul><li>React, Vite, Tailwind CSS, Recharts, Lucide React, Axios</li><li>Python, Flask, Flask-CORS, Pandas, NumPy</li><li>Scikit-learn Pipelines, ColumnTransformer, Random Forest</li><li>Joblib model artifacts and ReportLab PDF reports</li></ul></Panel>
      <Panel title="Severity labels"><div className="table-wrap"><table><thead><tr><th>Label</th><th>Category</th></tr></thead><tbody>{["Fatal", "Serious Injury", "Minor Injury", "Property Damage Only"].map((name, index) => <tr key={name}><td>{index + 1}</td><td>{name}</td></tr>)}</tbody></table></div></Panel>
      <Panel title="Important limitations"><ul><li>Generated data is synthetic, not official historical accident data.</li><li>Model predictions are educational only and can be wrong.</li><li>Patterns describe association and do not establish cause.</li><li>This app does not dispatch emergency services or make an official assessment.</li></ul></Panel>
    </div>
  </>;
}

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [filters, setFilters] = useState({});
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const filterKey = useMemo(() => JSON.stringify(filters), [filters]);
  useEffect(() => {
    if (page !== "dashboard") return;
    let active = true;
    setLoading(true);
    api.dashboard(paramsFrom(filters)).then((result) => {
      if (active) { setDashboard(result); setApiError(""); }
    }).catch((requestError) => { if (active) setApiError(errorMessage(requestError)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [page, filterKey]);
  const current = navigation.find((item) => item.id === page) || navigation[0];
  function navigate(id) { setPage(id); setMenuOpen(false); }
  const content = {
    dashboard: <DashboardPage data={dashboard} loading={loading} filters={filters} setFilters={setFilters} error={apiError} />,
    prediction: <PredictionPage />,
    analytics: <AnalyticsPage filters={filters} setFilters={setFilters} />,
    evaluation: <EvaluationPage />,
    batch: <BatchPage />,
    data: <DataPage />,
    about: <AboutPage />,
  }[page];

  return <div className="app-shell">
    <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
      <div className="brand"><div className="brand-mark"><Activity size={20} /></div><span>ROADWISE</span></div>
      <div className="nav-caption">Workspace</div>
      <nav>{navigation.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${page === id ? "active" : ""}`} onClick={() => navigate(id)}><Icon size={17} />{label}</button>)}</nav>
      <div className="sidebar-note">Learning project<br />Synthetic data · educational use only</div>
    </aside>
    <main className="main-area">
      <header className="topbar">
        <div className="flex items-center">
          <button className="mobile-menu" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle navigation"><Menu size={21} /></button>
          <div><div className="top-title">{current.label}</div><div className="top-subtitle">Smart accident analytics & severity prediction</div></div>
        </div>
        <div className="top-status"><span className={`status-dot ${apiError ? "bg-rose-500" : ""}`} />{apiError ? "Backend unavailable" : "Educational prototype"}</div>
      </header>
      <div className="content">{content}</div>
    </main>
  </div>;
}
