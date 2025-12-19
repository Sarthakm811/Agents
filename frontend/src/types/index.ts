export interface ResearchTopic {
  title: string;
  domain: string;
  keywords: string[];
  complexity: 'basic' | 'intermediate' | 'advanced';
  constraints?: Record<string, unknown>;
}

export interface ResearchConfig {
  topic: ResearchTopic;
  authorName: string;
  authorInstitution: string;
}

export interface ResearchMetrics {
  originalityScore: number;
  noveltyScore: number;
  plagiarismScore: number;
  ethicsScore: number;
  totalAgents: number;
  activeAgents: number;
  tasksCompleted: number;
  apiCalls: number;
}

export interface ResearchStage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: string;
  endTime?: string;
  results?: Record<string, unknown>;
}

export interface AgentActivity {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'working' | 'completed';
  currentTask?: string;
  tasksCompleted: number;
}

export interface ResearchSession {
  id: string;
  config: ResearchConfig;
  status: 'configuring' | 'running' | 'completed' | 'failed';
  stages: ResearchStage[];
  metrics: ResearchMetrics;
  agents: AgentActivity[];
  createdAt: string;
  updatedAt: string;
}


// Overall system metrics
export interface OverallMetrics {
  totalSessions: number;
  activeSessions: number;
  completedSessions: number;
  avgOriginalityScore: number;
  totalAgents: number;
  activeAgents: number;
}

// User settings and preferences
export interface UserPreferences {
  autoStartEthicsReview: boolean;
  enablePlagiarismDetection: boolean;
  realTimeNotifications: boolean;
}

export interface UserSettings {
  fullName: string;
  email: string;
  institution: string;
  preferences: UserPreferences;
}

// Compliance and ethics
export interface ComplianceCheck {
  name: string;
  status: 'passed' | 'failed' | 'warning';
}

export interface ComplianceCategory {
  name: string;
  score: number;
  status: 'passed' | 'failed' | 'warning';
  checks: ComplianceCheck[];
}

export interface ComplianceReport {
  sessionId: string;
  complianceScore: number;
  categories: ComplianceCategory[];
}

// Research results and paper details
export interface PaperSection {
  title: string;
  content: string;
}

export interface PaperDetails {
  abstract: string;
  sections: PaperSection[];
  citations: number;
  pages: number;
}

export interface ResearchResults {
  sessionId: string;
  title: string;
  author: string;
  institution: string;
  originalityScore: number;
  noveltyScore: number;
  ethicsScore: number;
  paper: PaperDetails;
}
