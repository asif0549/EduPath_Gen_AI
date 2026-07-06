import { FormEvent, useState } from "react";
import { ClassPrediction, predictStudent, StudentPrediction, StudentProfile } from "./api";

const initialProfile: StudentProfile = {
  attendance: 82,
  cgpa: 8.1,
  aptitude_score: 76,
  coding_score: 72,
  communication_score: 70,
  mock_exam_score: 74,
  backlogs: 0,
  career_interest: "Software Engineer",
  exam_selected: "GATE",
};

const numericFields: Array<{ key: keyof StudentProfile; label: string; max: number; step?: number }> = [
  { key: "attendance", label: "Attendance (%)", max: 100 },
  { key: "cgpa", label: "CGPA", max: 10, step: 0.01 },
  { key: "aptitude_score", label: "Aptitude score", max: 100 },
  { key: "coding_score", label: "Coding score", max: 100 },
  { key: "communication_score", label: "Communication score", max: 100 },
  { key: "mock_exam_score", label: "Mock exam score", max: 100 },
  { key: "backlogs", label: "Current backlogs", max: 50 },
];

const careerOptions = [
  "Software Engineer", "Data Scientist", "AI Researcher", "Cybersecurity",
  "Cloud Engineer", "Business Analyst",
];
const examOptions = ["GATE", "CAT", "GRE", "RRB-NTPC", "SkillsCert", "No exam"];

function ResultCard({ title, result }: { title: string; result: ClassPrediction }) {
  const confidence = Math.round(result.confidence * 100);
  return (
    <article className="result-card">
      <span className="eyebrow">{title}</span>
      <div className="result-heading">
        <h3>{result.prediction}</h3>
        <strong>{confidence}%</strong>
      </div>
      <div className="meter" aria-label={`${confidence}% confidence`}>
        <span style={{ width: `${confidence}%` }} />
      </div>
      <p>Model confidence</p>
    </article>
  );
}

export default function App() {
  const [profile, setProfile] = useState<StudentProfile>(initialProfile);
  const [result, setResult] = useState<StudentPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateNumber = (key: keyof StudentProfile, value: string) => {
    setProfile((current) => ({ ...current, [key]: Number(value) }));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      setResult(await predictStudent(profile));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach the API");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="EduPath AI home">
          <span>EP</span> EduPath AI
        </a>
        <span className="status"><i /> Decision intelligence online</span>
      </header>

      <section className="hero" id="top">
        <div>
          <span className="eyebrow">Student decision intelligence</span>
          <h1>Turn academic signals into your next best move.</h1>
          <p>Get placement outlook, backlog risk, and exam readiness in one focused assessment.</p>
        </div>
        <div className="hero-stat"><strong>3</strong><span>ML signals<br />one decision view</span></div>
      </section>

      <section className="workspace">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="section-title">
            <div><span className="step">01</span><h2>Student profile</h2></div>
            <p>Enter the latest verified scores.</p>
          </div>

          <div className="field-grid">
            {numericFields.map(({ key, label, max, step }) => (
              <label key={key}>
                <span>{label}</span>
                <input
                  type="number" min="0" max={max} step={step ?? 1} required
                  value={profile[key] as number}
                  onChange={(event) => updateNumber(key, event.target.value)}
                />
              </label>
            ))}
            <label>
              <span>Career interest</span>
              <select value={profile.career_interest} onChange={(e) => setProfile({ ...profile, career_interest: e.target.value })}>
                {careerOptions.map((option) => <option key={option}>{option}</option>)}
              </select>
            </label>
            <label>
              <span>Target exam</span>
              <select value={profile.exam_selected} onChange={(e) => setProfile({ ...profile, exam_selected: e.target.value })}>
                {examOptions.map((option) => <option key={option}>{option}</option>)}
              </select>
            </label>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Analyzing profile..." : "Generate intelligence report"}
          </button>
          {error && <p className="error" role="alert">{error}. Confirm the API is running on port 8000.</p>}
        </form>

        <section className="panel results-panel">
          <div className="section-title">
            <div><span className="step">02</span><h2>Decision report</h2></div>
            <p>Probabilities, not guarantees.</p>
          </div>
          {result ? (
            <div className="results">
              <ResultCard title="Placement outlook" result={result.placement} />
              <ResultCard title="Backlog risk" result={result.backlog_risk} />
              <ResultCard title="Exam readiness" result={result.exam_readiness} />
            </div>
          ) : (
            <div className="empty-state">
              <span>AI</span>
              <h3>Your report will appear here</h3>
              <p>Complete the profile and run the assessment to see all three predictions.</p>
            </div>
          )}
        </section>
      </section>

      {result && (
        <section className="roadmap panel">
          <div className="roadmap-head">
            <div>
              <span className="eyebrow">Your recommended future path</span>
              <h2>{result.roadmap.recommended_path}</h2>
              <p>{result.roadmap.summary}</p>
            </div>
            <div className="fit-score">
              <strong>{Math.round(result.roadmap.fit_score)}%</strong>
              <span>profile fit</span>
            </div>
          </div>

          <div className="roadmap-insights">
            <div>
              <span className="insight-label">Build on</span>
              {result.roadmap.strengths.map((strength) => <em key={strength}>{strength}</em>)}
            </div>
            <div>
              <span className="insight-label">Improve first</span>
              {result.roadmap.priority_gaps.map((gap) => <em key={gap}>{gap}</em>)}
            </div>
            <div>
              <span className="insight-label">Alternative paths</span>
              {result.roadmap.alternative_paths.map((path) => (
                <em key={path.career}>{path.career} · {Math.round(path.fit_score)}%</em>
              ))}
            </div>
          </div>

          <div className="timeline">
            {result.roadmap.steps.map((item, index) => (
              <article className="timeline-step" key={item.phase}>
                <div className="timeline-number">{String(index + 1).padStart(2, "0")}</div>
                <span className="eyebrow">{item.timeline} · {item.phase}</span>
                <h3>{item.focus}</h3>
                <ul>{item.actions.map((action) => <li key={action}>{action}</li>)}</ul>
                <p><strong>Target:</strong> {item.success_metric}</p>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
