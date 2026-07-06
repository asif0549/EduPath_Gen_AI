const API_URL = "https://edupathgenai-production.up.railway.app";
export interface StudentProfile {
  name?: string;
  degree?: string;
  branch?: string;
  semester?: number;
  primary_goal?: string;
  goal_context?: Record<string, string | number | boolean>;
  attendance: number;
  cgpa: number;
  aptitude_score: number;
  coding_score: number;
  communication_score: number;
  mock_exam_score: number;
  backlogs: number;
  career_interest?: string;
  exam_selected: string;
}

export interface ClassPrediction {
  prediction: string;
  confidence: number;
  probabilities: Record<string, number>;
  explanation_method: string;
  factors: FeatureImpact[];
}

export interface FeatureImpact {
  feature: string;
  value: string;
  baseline: string;
  effect: "supports" | "opposes" | "neutral";
  probability_change: number;
  reason: string;
}

export interface CareerFit {
  career: string;
  fit_score: number;
}

export interface RoadmapStep {
  phase: string;
  timeline: string;
  focus: string;
  actions: string[];
  success_metric: string;
}

export interface StudentRoadmap {
  recommended_path: string;
  fit_score: number;
  summary: string;
  strengths: string[];
  priority_gaps: string[];
  alternative_paths: CareerFit[];
  steps: RoadmapStep[];
}

export interface CareerRecommendation {
  career: string;
  suitability_score: number;
  confidence: number;
  why_recommended: string;
  pros: string[];
  challenges: string[];
  future_demand: string;
  salary_range: string;
  required_skills: string[];
  missing_skills: string[];
  time_to_job_ready: string;
  roadmap: string[];
}

export interface StudentPrediction {
  placement: ClassPrediction;
  backlog_risk: ClassPrediction;
  exam_readiness: ClassPrediction;
  roadmap: StudentRoadmap;
  career_recommendations: CareerRecommendation[];
}

const OFFLINE_DOCUMENT_KEY = "edupath_offline_documents";

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function makeFactors(profile: StudentProfile): FeatureImpact[] {
  const fields: Array<[keyof StudentProfile, string, string]> = [
    ["cgpa", "CGPA", "7"],
    ["coding_score", "Coding score", "65"],
    ["attendance", "Attendance", "75"],
  ];
  return fields.map(([key, label, base]) => {
    const value = profile[key] as number;
    const delta = clamp((value - Number(base)) / 100, -0.2, 0.2);
    const effect = delta > 0.02 ? "supports" : delta < -0.02 ? "opposes" : "neutral";
    return {
      feature: label,
      value: String(value),
      baseline: base,
      effect,
      probability_change: Number(delta.toFixed(3)),
      reason: `Compared with a typical baseline of ${base}, this value ${effect === "supports" ? "supports" : effect === "opposes" ? "opposes" : "is neutral for"} the prediction.`,
    };
  });
}

function buildPrediction(profile: StudentProfile, label: string, score: number, positiveLabel: string, negativeLabel: string): ClassPrediction {
  const probability = clamp(score, 0.05, 0.95);
  return {
    prediction: probability >= 0.5 ? positiveLabel : negativeLabel,
    confidence: Number(probability.toFixed(3)),
    probabilities: {
      [positiveLabel]: Number(probability.toFixed(3)),
      [negativeLabel]: Number((1 - probability).toFixed(3)),
    },
    explanation_method: "Offline local estimate based on user profile.",
    factors: makeFactors(profile),
  };
}

function getCareerWeight(profile: StudentProfile, career: string) {
  const interest = profile.career_interest?.toLowerCase() || "";
  const base = {
    "software engineer": 1.0,
    "data scientist": 1.0,
    "ai researcher": 1.0,
    "cybersecurity": 1.0,
    "cloud engineer": 1.0,
    "business analyst": 1.0,
  }[career.toLowerCase()] ?? 1.0;
  const interestBonus = interest && career.toLowerCase().includes(interest.toLowerCase()) ? 1.1 : 1.0;
  return base * interestBonus;
}

function makeCareerRecommendations(profile: StudentProfile): CareerRecommendation[] {
  const careerList = [
    "Software Engineer",
    "Data Scientist",
    "AI Researcher",
    "Cybersecurity",
    "Cloud Engineer",
    "Business Analyst",
  ];
  const baseScore = profile.coding_score * 0.3 + profile.aptitude_score * 0.25 + profile.cgpa * 7 * 0.15 + profile.communication_score * 0.15 + profile.attendance * 0.15;
  const recommendations = careerList.map((career) => {
    const weight = getCareerWeight(profile, career);
    const score = clamp((baseScore * weight) / 1.4, 0, 100);
    return {
      career,
      suitability_score: Number(score.toFixed(1)),
      confidence: Number((0.6 + (score / 100) * 0.35).toFixed(3)),
      why_recommended: `This path fits your current strengths and goal of ${profile.primary_goal || "growth"}.`,
      pros: ["Clear study path", "High growth potential", "Strong market demand"],
      challenges: ["Needs focused practice", "Competitive roles", "Requires strong portfolio"],
      future_demand: "Growing demand over the next 3 years",
      salary_range: "₹4L - ₹14L",
      required_skills: ["Problem solving", "Communication", "Project experience"],
      missing_skills: ["Advanced projects", "Interview practice"],
      time_to_job_ready: "3-6 months",
      roadmap: ["Strengthen fundamentals", "Build one portfolio project", "Apply to relevant roles"],
    };
  });
  return recommendations.sort((a, b) => b.suitability_score - a.suitability_score).slice(0, 3);
}

function buildStudentPrediction(profile: StudentProfile): StudentPrediction {
  const placementScore = clamp((profile.cgpa * 10) * 0.08 + profile.coding_score * 0.25 + profile.aptitude_score * 0.22 + profile.communication_score * 0.15 + profile.attendance * 0.2 + profile.mock_exam_score * 0.1, 0, 1);
  const backlogScore = clamp(1 - (profile.backlogs > 0 ? 0.4 : 0) - profile.attendance * 0.003 + profile.cgpa * -0.01, 0, 1);
  const examScore = clamp(profile.mock_exam_score * 0.4 + profile.aptitude_score * 0.25 + profile.coding_score * 0.15 + profile.cgpa * 7 * 0.05 + profile.attendance * 0.15, 0, 1);

  return {
    placement: buildPrediction(profile, profile.backlogs > 1 ? "Not Placed" : "Placed", placementScore, "Placed", "Not Placed"),
    backlog_risk: buildPrediction(profile, profile.backlogs > 1 ? "High Risk" : "Low Risk", 1 - backlogScore, "High Risk", "Low Risk"),
    exam_readiness: buildPrediction(profile, profile.mock_exam_score > 65 ? "Ready" : "Needs Improvement", examScore, "Ready", "Needs Improvement"),
    roadmap: {
      recommended_path: makeCareerRecommendations(profile)[0]?.career ?? "Software Engineer",
      fit_score: Number(clamp((placementScore + examScore) / 2 * 100, 0, 100).toFixed(1)),
      summary: `Based on your current scores and goal, this is the strongest path to focus on over the next 90 days.`,
      strengths: [profile.coding_score >= 70 ? "Coding" : "Problem solving", profile.aptitude_score >= 70 ? "Aptitude" : "Learning agility"],
      priority_gaps: [profile.backlogs > 0 ? "Backlog clearance" : "Portfolio depth", profile.communication_score < 70 ? "Communication" : "Advanced concepts"].filter(Boolean),
      alternative_paths: makeCareerRecommendations(profile).slice(1, 3).map((career) => ({ career: career.career, fit_score: career.suitability_score })),
      steps: [
        {
          phase: "Foundation",
          timeline: "Weeks 1–4",
          focus: "Close the biggest gap",
          actions: [profile.backlogs > 0 ? "Complete backlog recovery plan" : "Strengthen core concepts", "Practice problems every day"],
          success_metric: "Demonstrate measurable improvement in the weakest signal.",
        },
        {
          phase: "Proof of skill",
          timeline: "Weeks 5–8",
          focus: "Build evidence and confidence",
          actions: ["Finish one portfolio project", "Review mistakes from mock assessments"],
          success_metric: "Complete at least two evaluative projects or mocks.",
        },
        {
          phase: "Launch",
          timeline: "Weeks 9–12",
          focus: "Convert readiness into opportunities",
          actions: ["Apply to targeted roles", "Prepare for interviews"],
          success_metric: "Secure interviews or mentor feedback sessions.",
        },
      ],
    },
    career_recommendations: makeCareerRecommendations(profile),
  };
}

export async function predictStudent(
  profile: StudentProfile
): Promise<StudentPrediction> {
  const response = await fetch(
    `${API_URL}/api/v1/predictions/student`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profile),
    }
  );

  if (!response.ok) {
    throw new Error("Prediction failed");
  }

  return await response.json();
}

export interface DocumentInfo {
  filename: string;
  size: number;
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/api/v1/documents/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error("Upload failed");
  }

  return await response.json();
}

export async function listDocuments(): Promise<string[]> {
  const response = await fetch(`${API_URL}/api/v1/documents`);

  if (!response.ok) {
    throw new Error("Failed to fetch documents");
  }

  const data = await response.json();
  return data.files;
}

export interface AssistantRequest {
  text?: string;
  profile?: StudentProfile;
}

export interface AssistantResponse {
  reply: string;
  recommendations?: any;
}

export async function assistantMessage(
  payload: AssistantRequest
): Promise<AssistantResponse> {
  const response = await fetch(
    `${API_URL}/api/v1/assistant`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error("Assistant request failed");
  }

  return await response.json();
}