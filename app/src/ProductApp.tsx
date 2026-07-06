import { FormEvent, useMemo, useState, useEffect } from "react";
import { predictStudent, StudentPrediction, StudentProfile, uploadDocument, listDocuments, assistantMessage } from "./api";

type Goal = "Campus Placement" | "Government Job" | "Higher Studies" | "AI Research" | "Cloud / DevOps" | "Undecided";

const goals: Array<{ name: Goal; icon: string; copy: string }> = [
  { name: "Campus Placement", icon: "01", copy: "Roles, interviews and placement readiness" },
  { name: "Government Job", icon: "02", copy: "Exam strategy, speed and mock performance" },
  { name: "Higher Studies", icon: "03", copy: "Academic profile and entrance preparation" },
  { name: "AI Research", icon: "04", copy: "ML foundations, research and project depth" },
  { name: "Cloud / DevOps", icon: "05", copy: "Cloud skills, labs and certification path" },
  { name: "Undecided", icon: "06", copy: "Discover the strongest path from your signals" },
];

const initial: StudentProfile = {
  name: "", degree: "B.Tech", branch: "Computer Science", semester: 6,
  primary_goal: "Undecided", goal_context: {}, attendance: 82, cgpa: 8.1,
  aptitude_score: 76, coding_score: 72, communication_score: 70,
  mock_exam_score: 74, backlogs: 0, exam_selected: "GATE", career_interest: "Undecided",
};

const adaptive: Record<Goal, Array<{ key: string; label: string; type?: "number"; placeholder: string }>> = {
  "Campus Placement": [
    { key: "projects", label: "Production-ready projects", type: "number", placeholder: "2" },
    { key: "internships", label: "Internships completed", type: "number", placeholder: "1" },
    { key: "github", label: "GitHub / portfolio URL", placeholder: "github.com/yourname" },
  ],
  "Government Job": [
    { key: "attempts", label: "Previous attempts", type: "number", placeholder: "0" },
    { key: "accuracy", label: "Average mock accuracy (%)", type: "number", placeholder: "72" },
    { key: "weak_subject", label: "Weakest subject", placeholder: "Quantitative aptitude" },
  ],
  "Higher Studies": [
    { key: "target_country", label: "Preferred destination", placeholder: "India / US / Europe" },
    { key: "research_projects", label: "Research projects", type: "number", placeholder: "1" },
    { key: "target_program", label: "Target program", placeholder: "MS Computer Science" },
  ],
  "AI Research": [
    { key: "ml_level", label: "ML knowledge", placeholder: "Beginner / Intermediate / Advanced" },
    { key: "papers", label: "Papers read this month", type: "number", placeholder: "3" },
    { key: "research_projects", label: "Research projects", type: "number", placeholder: "1" },
  ],
  "Cloud / DevOps": [
    { key: "cloud_platform", label: "Cloud platform practiced", placeholder: "Google Cloud" },
    { key: "labs", label: "Hands-on labs completed", type: "number", placeholder: "8" },
    { key: "certifications", label: "Certifications earned", type: "number", placeholder: "0" },
  ],
  Undecided: [
    { key: "enjoyed_subject", label: "Subject you enjoy most", placeholder: "Algorithms" },
    { key: "work_style", label: "Preferred work style", placeholder: "Building / Research / People" },
    { key: "priority", label: "Top priority", placeholder: "Growth / Stability / Impact" },
  ],
};

const skills = ["Aptitude", "Coding", "Communication", "Academics", "Attendance", "Exam"];

function Radar({ profile }: { profile: StudentProfile }) {
  const values = [profile.aptitude_score, profile.coding_score, profile.communication_score, profile.cgpa * 10, profile.attendance, profile.mock_exam_score];
  const points = values.map((value, index) => {
    const angle = -Math.PI / 2 + index * Math.PI / 3;
    const radius = value * 0.72;
    return `${100 + Math.cos(angle) * radius},${100 + Math.sin(angle) * radius}`;
  }).join(" ");
  return (
    <div className="radar-wrap">
      <svg viewBox="0 0 200 200" aria-label="Student skill radar">
        {[24, 48, 72].map((r) => <circle key={r} cx="100" cy="100" r={r} className="radar-ring" />)}
        {skills.map((_, i) => { const a = -Math.PI / 2 + i * Math.PI / 3; return <line key={i} x1="100" y1="100" x2={100 + Math.cos(a) * 72} y2={100 + Math.sin(a) * 72} className="radar-axis" />; })}
        <polygon points={points} className="radar-shape" />
      </svg>
      <div className="radar-legend">{skills.map((skill, i) => <span key={skill}><i style={{ opacity: .45 + i * .08 }} />{skill}</span>)}</div>
    </div>
  );
}

export default function ProductApp() {
  const [profile, setProfile] = useState<StudentProfile>(initial);
  const [step, setStep] = useState(1);
  const [result, setResult] = useState<StudentPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [view, setView] = useState<"profile" | "pathway" | "progress" | "documents" | "advisor">("profile");
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [assistantHistory, setAssistantHistory] = useState<Array<{role: string; text: string}>>([]);
  const [signedIn, setSignedIn] = useState(false);
  const [authPage, setAuthPage] = useState<"signIn" | "signUp">("signIn");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const goal = (profile.primary_goal || "Undecided") as Goal;
  const score = useMemo(() => result ? Math.round((result.placement.confidence + result.exam_readiness.confidence) * 50) : 0, [result]);

  const setValue = (key: keyof StudentProfile, value: string | number) => setProfile((p) => ({ ...p, [key]: value }));
  const goNextStep = () => setStep((current) => Math.min(3, current + 1));
  const goPreviousStep = () => setStep((current) => Math.max(1, current - 1));
  const analyze = async (event: FormEvent) => {
    event.preventDefault(); setLoading(true); setError("");
    try { setResult(await predictStudent(profile)); setStep(4); }
    catch (e) { setError(e instanceof Error ? e.message : "Analysis failed"); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (view === "documents") {
      listDocuments().then(setUploadedFiles).catch(() => setUploadedFiles([]));
    }
  }, [view]);

  const handleUpload = async (file: File | null) => {
    if (!file) return;
    try {
      await uploadDocument(file);
      setUploadedFiles(await listDocuments());
    } catch (e) {
      console.error(e);
      alert("Upload failed");
    }
  };

  const handleAuthSubmit = (event: FormEvent) => {
    event.preventDefault();
    const email = authEmail.trim();
    if (!email) return;
    const username = email.split(/[@\s]/)[0] || email;
    setProfile((current) => ({ ...current, name: username.charAt(0).toUpperCase() + username.slice(1) }));
    setSignedIn(true);
    setAuthPassword("");
  };

  const sendAssistant = async (text: string) => {
    if (!text) return;
    setAssistantHistory((h) => [...h, { role: "user", text }]);
    try {
      const resp = await assistantMessage({ text, profile });
      setAssistantHistory((h) => [...h, { role: "assistant", text: resp.reply }]);
    } catch (e) {
      setAssistantHistory((h) => [...h, { role: "assistant", text: "Assistant error" }]);
    }
  };

  function AssistantInput({ onSend }: { onSend: (text: string) => void }) {
    const [value, setValue] = useState("");
    return (
      <form onSubmit={(e) => { e.preventDefault(); onSend(value); setValue(""); }}>
        <input placeholder="Ask the AI advisor a question" value={value} onChange={(e) => setValue(e.target.value)} style={{width:'80%', marginRight:8}} />
        <button type="submit">Send</button>
      </form>
    );
  }

  if (!signedIn) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="auth-brand">
            <strong>EduPath AI</strong>
            <span>Student decision intelligence</span>
          </div>
          <div className="auth-toggle">
            <button type="button" className={authPage === "signIn" ? "active" : ""} onClick={() => setAuthPage("signIn")}>Sign in</button>
            <button type="button" className={authPage === "signUp" ? "active" : ""} onClick={() => setAuthPage("signUp")}>Sign up</button>
          </div>
          <form className="auth-form" onSubmit={handleAuthSubmit}>
            <label>
              <span>Email address</span>
              <input
                type="email"
                placeholder="you@example.com"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                required
              />
            </label>
            <label>
              <span>Password</span>
              <input
                type="password"
                placeholder="Create a password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
              />
            </label>
            <p className="auth-note">Passwords are not verified; any email lets you continue.</p>
            <button type="submit" className="auth-submit">
              {authPage === "signIn" ? "Continue to EduPath" : "Create account"}
            </button>
          </form>
          <div className="auth-footer">
            {authPage === "signIn" ? (
              <p>Don’t have an account? <button type="button" onClick={() => setAuthPage("signUp")}>Sign up</button></p>
            ) : (
              <p>Already have an account? <button type="button" onClick={() => setAuthPage("signIn")}>Sign in</button></p>
            )}
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="product-shell">
      <aside className="side-nav">
        <div className="side-brand"><b>E</b><span>EduPath<small>Decision Intelligence</small></span></div>
        <nav>
          <button className={view === "pathway" ? "active" : ""} onClick={() => setView("pathway")}><span>⌁</span>My pathway</button>
          <button className={view === "progress" ? "active" : ""} onClick={() => setView("progress")}><span>◫</span>Progress</button>
          <button className={view === "documents" ? "active" : ""} onClick={() => setView("documents")}><span>◇</span>Documents</button>
          <button className={view === "advisor" ? "active" : ""} onClick={() => setView("advisor")}><span>◎</span>AI advisor</button>
        </nav>
        <button className={"side-bottom" + (view === "profile" ? " active" : "")} type="button" onClick={() => setView("profile")}>        
          <div>
            <span>{profile.name ? `${profile.name.split(" ")[0]}'s dashboard` : "Student dashboard"}</span>
            <b>{profile.name ? profile.name.slice(0, 2).toUpperCase() : "ST"}</b>
          </div>
        </button>
      </aside>

      <main className="product-main">
        <header className="product-top">
          <div><span>STUDENT WORKSPACE</span><strong>{result ? "Your future pathway" : "Build your pathway"}</strong></div>
          <div className="secure-pill"><i /> AI models online</div>
        </header>

        {view === "pathway" && (
          !result ? (
          <div className="onboarding">
            <div className="onboard-intro">
              <span className="kicker">PERSONALIZED ASSESSMENT</span>
              <h1>Let’s map the future that fits <em>you.</em></h1>
              <p>Three focused steps. No generic questionnaire. Your answers shape what we ask next.</p>
            </div>
            <div className="stepper">{["Profile", "Goal", "Signals"].map((label, i) => <div className={step >= i + 1 ? "done" : ""} key={label}><b>{step > i + 1 ? "✓" : i + 1}</b><span>{label}</span></div>)}</div>

            <form className="onboard-card" onSubmit={analyze}>
              {step === 1 && <>
                <div className="card-heading"><span>01 / ABOUT YOU</span><h2>Start with the academic basics</h2><p>This creates your baseline. You can update it every semester.</p></div>
                <div className="modern-grid">
                  <label className="wide">Full name<input required placeholder="Your name" value={profile.name} onChange={(e) => setValue("name", e.target.value)} /></label>
                  <label>Degree<select value={profile.degree} onChange={(e) => setValue("degree", e.target.value)}><option>B.Tech</option><option>B.Sc</option><option>BCA</option><option>M.Tech</option><option>MCA</option></select></label>
                  <label>Branch<input value={profile.branch} onChange={(e) => setValue("branch", e.target.value)} /></label>
                  <label>Semester<input type="number" min="1" max="12" value={profile.semester} onChange={(e) => setValue("semester", +e.target.value)} /></label>
                  <label>CGPA<input type="number" min="0" max="10" step=".01" value={profile.cgpa} onChange={(e) => setValue("cgpa", +e.target.value)} /></label>
                  <label>Attendance %<input type="number" min="0" max="100" value={profile.attendance} onChange={(e) => setValue("attendance", +e.target.value)} /></label>
                  <label>Active backlogs<input type="number" min="0" value={profile.backlogs} onChange={(e) => setValue("backlogs", +e.target.value)} /></label>
                </div>
              </>}

              {step === 2 && <>
                <div className="card-heading"><span>02 / YOUR DIRECTION</span><h2>What outcome matters most right now?</h2><p>We’ll adapt the final questions to your goal. This does not force the recommendation.</p></div>
                <div className="goal-grid">{goals.map((item) => <button type="button" className={goal === item.name ? "selected" : ""} key={item.name} onClick={() => setValue("primary_goal", item.name)}><i>{item.icon}</i><strong>{item.name}</strong><span>{item.copy}</span></button>)}</div>
              </>}

              {step === 3 && <>
                <div className="card-heading"><span>03 / PERFORMANCE SIGNALS</span><h2>Now, the evidence behind your path</h2><p>Questions adapted for <strong>{goal}</strong>. Career ranking remains performance-based.</p></div>
                <div className="signal-layout">
                  <div className="score-stack">
                    {[['aptitude_score','Aptitude'],['coding_score','Coding'],['communication_score','Communication'],['mock_exam_score','Latest mock']].map(([key,label]) => <label key={key}><span>{label}<b>{profile[key as keyof StudentProfile] as number}</b></span><input type="range" min="0" max="100" value={profile[key as keyof StudentProfile] as number} onChange={(e) => setValue(key as keyof StudentProfile, +e.target.value)} /></label>)}
                  </div>
                  <div className="adaptive-box"><span>ADAPTED TO YOUR GOAL</span>{adaptive[goal].map((field) => <label key={field.key}>{field.label}<input type={field.type || "text"} placeholder={field.placeholder} onChange={(e) => setProfile((p) => ({ ...p, goal_context: { ...p.goal_context, [field.key]: field.type === "number" ? +e.target.value : e.target.value } }))} /></label>)}</div>
                </div>
              </>}

              {error && <p className="form-error">{error}. Check that the API is running.</p>}
              <div className="form-actions">{step > 1 && <button type="button" className="ghost" onClick={goPreviousStep}>Back</button>}<button type={step === 3 ? "submit" : "button"} className="primary-action" onClick={step === 3 ? undefined : goNextStep}>{step === 3 ? (loading ? "Building your pathway..." : "Reveal my best path") : "Continue"}<span>→</span></button></div>
            </form>
          </div>
        ) : null
      )}
        {view === "pathway" && result && (
          <div className="path-dashboard">
            <section className="welcome-row"><div><span className="kicker">YOUR DECISION BRIEF</span><h1>{profile.name ? `${profile.name.split(" ")[0]}, here’s` : "Here’s"} your strongest path.</h1><p>Built from your academic signals, skill profile and current goal.</p></div><button className="edit-profile" onClick={() => { setResult(null); setStep(1); }}>Update profile</button></section>
            <section className="path-hero"><div className="path-rank">#1 PATH MATCH</div><div className="path-copy"><span>RECOMMENDED DIRECTION</span><h2>{result.roadmap.recommended_path}</h2><p>{result.roadmap.summary}</p><div className="path-tags">{result.roadmap.strengths.map((s) => <b key={s}>✓ {s}</b>)}</div></div><div className="match-orbit"><strong>{Math.round(result.roadmap.fit_score)}%</strong><span>PATH FIT</span></div></section>
            <section className="intelligence-grid">
              <article className="skill-panel dashboard-panel"><div className="panel-title"><span>SKILL SHAPE</span><b>Performance profile</b></div><Radar profile={profile} /></article>
              <article className="readiness-panel dashboard-panel"><div className="panel-title"><span>READINESS</span><b>Current outlook</b></div><div className="readiness-score"><div style={{ "--score": `${score * 3.6}deg` } as React.CSSProperties}><strong>{score}</strong><span>/100</span></div><p>Composite readiness</p></div><div className="mini-signals"><span>Placement<b>{result.placement.prediction}</b></span><span>Academic risk<b>{result.backlog_risk.prediction}</b></span><span>Exam<b>{result.exam_readiness.prediction}</b></span></div></article>
              <article className="gap-panel dashboard-panel"><div className="panel-title"><span>FOCUS NOW</span><b>Highest-impact gaps</b></div>{result.roadmap.priority_gaps.map((gap, i) => <div className="gap-row" key={gap}><i>0{i + 1}</i><span>{gap}<small>{i === 0 ? "Start here — highest leverage" : "Build into weekly practice"}</small></span></div>)}</article>
            </section>
            <section className="evidence-board">
              <div className="evidence-title"><div><span className="kicker">MODEL EVIDENCE</span><h2>Why the models reached these decisions</h2></div><p>Local sensitivity against training-data baselines. These are model effects, not causal claims.</p></div>
              <div className="evidence-grid">
                {[
                  ["Placement", result.placement],
                  ["Backlog risk", result.backlog_risk],
                  ["Exam readiness", result.exam_readiness],
                ].map(([label, prediction]) => {
                  const item = prediction as typeof result.placement;
                  return <article key={label as string}><header><span>{label as string}</span><b>{item.prediction}</b></header>{item.factors.slice(0, 3).map((factor) => <div className="factor-row" key={factor.feature}><i className={factor.effect}>{factor.effect === "supports" ? "+" : factor.effect === "opposes" ? "−" : "·"}</i><span><b>{factor.feature}</b><small>Your value {factor.value} · baseline {factor.baseline}</small></span><strong>{factor.probability_change > 0 ? "+" : ""}{(factor.probability_change * 100).toFixed(1)} pp</strong></div>)}</article>;
                })}
              </div>
            </section>
            <section className="roadmap-board"><div className="roadmap-title"><span className="kicker">YOUR 90-DAY EXECUTION PLAN</span><h2>From signal to momentum.</h2><p>Each phase has one focus and a measurable finish line.</p></div><div className="path-line">{result.roadmap.steps.map((item, i) => <article key={item.phase}><div className="phase-dot">{i + 1}</div><span>{item.timeline}</span><h3>{item.phase}</h3><h4>{item.focus}</h4><ul>{item.actions.map((a) => <li key={a}>{a}</li>)}</ul><p><b>Success looks like</b>{item.success_metric}</p></article>)}</div></section>
            <section className="evidence-board">
              <div className="evidence-title"><div><span className="kicker">PERSONALIZED CAREER RECOMMENDATIONS</span><h2>Top 3 career paths for you</h2></div><p>These recommendations are generated from your profile, the prediction models, and the decision engine.</p></div>
              <div className="evidence-grid">
                {result.career_recommendations.map((career) => (
                  <article key={career.career}>
                    <header><span>{career.career}</span><b>{Math.round(career.suitability_score)}%</b></header>
                    <div className="factor-row"><span><b>Why recommended</b><small>{career.why_recommended}</small></span></div>
                    <div className="factor-row"><span><b>Pros</b><small>{career.pros.join(" • ")}</small></span></div>
                    <div className="factor-row"><span><b>Challenges</b><small>{career.challenges.join(" • ")}</small></span></div>
                    <div className="factor-row"><span><b>Required skills</b><small>{career.required_skills.join(", ")}</small></span></div>
                    <div className="factor-row"><span><b>Missing skills</b><small>{career.missing_skills.join(", ")}</small></span></div>
                    <div className="factor-row"><span><b>Roadmap</b><small>{career.roadmap.join(" → ")}</small></span></div>
                    <div className="factor-row"><span><b>Demand / salary</b><small>{career.future_demand} · {career.salary_range}</small></span></div>
                  </article>
                ))}
              </div>
            </section>
            <section className="alternatives"><div><span className="kicker">KEEP THESE IN VIEW</span><h2>Strong alternative paths</h2></div>{result.roadmap.alternative_paths.map((path, i) => <article key={path.career}><span>0{i + 2}</span><b>{path.career}</b><strong>{Math.round(path.fit_score)}% fit</strong></article>)}</section>
          </div>
        )}

        {view === "profile" && (
          <section className="panel profile-panel">
            <div className="section-title">
              <div><span className="step">01</span><h2>Profile dashboard</h2></div>
              <p>See your current plan, analytics, and career roadmap in one place.</p>
            </div>
            <div className="profile-top">
              <div className="profile-summary">
                <span>Welcome back,</span>
                <h2>{profile.name || "Student"}</h2>
                <p>{profile.primary_goal || "Undecided"} · {profile.degree}, Semester {profile.semester}</p>
                <div className="profile-badges">
                  <strong>{profile.exam_selected}</strong>
                  <strong>{profile.career_interest}</strong>
                </div>
              </div>
              <div className="profile-actions">
                <button type="button" onClick={() => setView("pathway")}>Go to pathway</button>
                <button type="button" className="ghost" onClick={() => { setSignedIn(false); setView("profile"); }}>Sign out</button>
              </div>
            </div>
            {result ? (
              <div className="profile-grid">
                <article>
                  <h3>Current career fit</h3>
                  <p>{result.roadmap.recommended_path}</p>
                  <span>{Math.round(result.roadmap.fit_score)}% fit</span>
                </article>
                <article>
                  <h3>Top stats</h3>
                  <ul>
                    <li>Placement outlook: {result.placement.prediction}</li>
                    <li>Exam readiness: {result.exam_readiness.prediction}</li>
                    <li>Backlog risk: {result.backlog_risk.prediction}</li>
                  </ul>
                </article>
                <article>
                  <h3>Roadmap highlights</h3>
                  <ol>
                    {result.roadmap.steps.map((item) => (
                      <li key={item.phase}><strong>{item.phase}:</strong> {item.focus}</li>
                    ))}
                  </ol>
                </article>
                <article>
                  <h3>Top career paths</h3>
                  <ol>
                    {result.career_recommendations.slice(0, 3).map((career) => (
                      <li key={career.career}>{career.career} — {Math.round(career.suitability_score)}%</li>
                    ))}
                  </ol>
                </article>
              </div>
            ) : (
              <div className="empty-state"><h3>Dashboard is ready</h3><p>Run the pathway assessment to load your analytics and roadmap.</p></div>
            )}
          </section>
        )}

        {view === "progress" && (
          <section className="panel results-panel">
            <div className="section-title">
              <div><span className="step">02</span><h2>Progress & metrics</h2></div>
              <p>Visualize your performance signals, career fit, and roadmap progress.</p>
            </div>
            {result ? (
              <div className="results">
                <div className="dashboard-panel">
                  <h3>Composite readiness</h3>
                  <p>Placement outlook: {result.placement.prediction} · {Math.round(result.placement.confidence * 100)}%</p>
                  <p>Exam readiness: {result.exam_readiness.prediction} · {Math.round(result.exam_readiness.confidence * 100)}%</p>
                  <p>Backlog risk: {result.backlog_risk.prediction} · {Math.round(result.backlog_risk.confidence * 100)}%</p>
                </div>
                <div className="dashboard-panel">
                  <h3>Skill radar</h3>
                  <Radar profile={profile} />
                </div>
                <div className="dashboard-panel">
                  <h3>Roadmap summary</h3>
                  <p>{result.roadmap.summary}</p>
                  <ul>
                    {result.roadmap.steps.map((stepItem) => (
                      <li key={stepItem.phase}><strong>{stepItem.phase}:</strong> {stepItem.focus}</li>
                    ))}
                  </ul>
                </div>
                <div className="dashboard-panel">
                  <h3>Top career recommendations</h3>
                  <ol>
                    {result.career_recommendations.slice(0, 3).map((career) => (
                      <li key={career.career}><strong>{career.career}</strong> — {Math.round(career.suitability_score)}% fit</li>
                    ))}
                  </ol>
                </div>
              </div>
            ) : (
              <div className="empty-state"><h3>No analysis yet</h3><p>Run the assessment to populate progress.</p></div>
            )}
          </section>
        )}

        {view === "documents" && (
          <section className="panel results-panel">
            <div className="section-title">
              <div><span className="step">03</span><h2>Documents</h2></div>
              <p>Upload resume, transcripts and certificates for analysis.</p>
            </div>
            <div className="onboard-card">
              <input type="file" onChange={(e) => handleUpload(e.target.files?.[0] ?? null)} />
              <h4>Uploaded files</h4>
              <ul>{uploadedFiles.map((f) => <li key={f}>{f}</li>)}</ul>
            </div>
          </section>
        )}

        {view === "advisor" && (
          <section className="panel results-panel">
            <div className="section-title">
              <div><span className="step">04</span><h2>AI advisor</h2></div>
              <p>Ask questions about your profile and recommendations.</p>
            </div>
            <div className="onboard-card">
              <div style={{minHeight:120, maxHeight:300, overflow:'auto'}}>
                {assistantHistory.map((m,i) => <div key={i} style={{marginBottom:8}}><b>{m.role}</b>: {m.text}</div>)}
              </div>
              <AssistantInput onSend={sendAssistant} />
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
