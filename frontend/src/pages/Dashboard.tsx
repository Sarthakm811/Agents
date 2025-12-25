import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import {
  Activity,
  FileText,
  TrendingUp,
  Users,
  AlertCircle,
  RefreshCw,
  CheckCircle2,
  PauseCircle,
  XCircle
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useOverallMetrics } from '@/hooks/useMetrics';
import { useResearchSession, useResearchSessions } from '@/hooks/useResearchSessions';
import type { AgentActivity } from '@/types';

export function Dashboard() {
  const { data: metrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useOverallMetrics();
  const { data: sessions, isLoading: sessionsLoading, error: sessionsError, refetch: refetchSessions } = useResearchSessions();

  const latestSession = sessions?.[ 0 ];
  const latestSessionId = latestSession?.id ?? '';
  const { data: sessionDetail } = useResearchSession(latestSessionId);

  const sessionMetrics = sessionDetail?.metrics ?? latestSession?.metrics;

  const metricScores = [
    { label: 'Originality', value: sessionMetrics?.originalityScore ?? 94, gradient: 'from-primary/70 via-primary/60 to-primary/40' },
    { label: 'Novelty', value: sessionMetrics?.noveltyScore ?? 88, gradient: 'from-secondary/70 via-secondary/60 to-secondary/40' },
    { label: 'Ethics', value: sessionMetrics?.ethicsScore ?? 92, gradient: 'from-emerald-400/70 via-emerald-400/60 to-emerald-400/40' },
    { label: 'Plagiarism (lower is better)', value: 100 - (sessionMetrics?.plagiarismScore ?? 6), gradient: 'from-accent/70 via-accent/60 to-accent/40' },
  ];

  const taskStats = [
    { label: 'Tasks Completed', value: sessionMetrics?.tasksCompleted ?? 0 },
    { label: 'API Calls', value: sessionMetrics?.apiCalls ?? 0 },
  ];

  const defaultAgents: AgentActivity[] = [
    { id: 'literature', name: 'Literature Agent', type: 'research', status: 'idle', currentTask: 'Standing by', tasksCompleted: 0 },
    { id: 'hypothesis', name: 'Hypothesis Agent', type: 'analysis', status: 'idle', currentTask: 'Standing by', tasksCompleted: 0 },
    { id: 'methodology', name: 'Methodology Agent', type: 'planning', status: 'idle', currentTask: 'Standing by', tasksCompleted: 0 },
    { id: 'writing', name: 'Writing Agent', type: 'writing', status: 'idle', currentTask: 'Standing by', tasksCompleted: 0 },
    { id: 'ethics', name: 'Ethics Agent', type: 'ethics', status: 'idle', currentTask: 'Standing by', tasksCompleted: 0 },
  ];

  const sessionAgents = sessionDetail?.agents ?? latestSession?.agents;
  const agentList = (sessionAgents ?? defaultAgents).slice(0, 8);

  const statusDot = {
    idle: 'bg-muted-foreground/40',
    working: 'bg-secondary',
    completed: 'bg-primary',
    failed: 'bg-destructive'
  } as const;

  const statusBadge = {
    idle: 'secondary',
    working: 'default',
    completed: 'outline',
    failed: 'destructive'
  } as const;

  const statusIcon = {
    idle: PauseCircle,
    working: Activity,
    completed: CheckCircle2,
    failed: XCircle
  } as const;

  const systemSignals = [
    { label: 'Total Sessions', value: metrics?.totalSessions ?? 0 },
    { label: 'Active Agents', value: metrics?.activeAgents ?? 0 },
    { label: 'Avg Originality', value: `${Math.round(metrics?.avgOriginalityScore ?? 94)}%` },
  ];

  const liveSignals = [
    { label: 'Ingestion latency', value: '120ms', intensity: 72 },
    { label: 'Queue depth', value: '8 tasks', intensity: 48 },
    { label: 'API throughput', value: '324 rpm', intensity: 64 },
    { label: 'Retry rate', value: '0.8%', intensity: 22 },
  ];

  // Build stats with defaults
  const stats = [
    {
      title: 'Active Sessions',
      value: String(metrics?.activeSessions ?? 0),
      change: '+12%',
      icon: Activity,
    },
    {
      title: 'Papers Generated',
      value: String(metrics?.completedSessions ?? 0),
      change: '+8%',
      icon: FileText,
    },
    {
      title: 'Avg Originality',
      value: `${Math.round(metrics?.avgOriginalityScore ?? 94)}%`,
      change: '+3%',
      icon: TrendingUp,
    },
    {
      title: 'Active Agents',
      value: String(metrics?.activeAgents ?? 0),
      change: '+5',
      icon: Users,
    },
  ];

  return (
    <div className="relative space-y-8 p-4 md:p-6">
      {/* Animated background orbs */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute left-12 top-16 h-72 w-72 rounded-full bg-primary/10 blur-3xl float-animate" />
        <div className="absolute right-10 bottom-24 h-80 w-80 rounded-full bg-secondary/10 blur-3xl float-animate" style={{ animationDelay: '1.2s' }} />
        <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/10 blur-3xl float-animate" style={{ animationDelay: '2s' }} />
      </div>

      {/* Hero + Stats */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border bg-gradient-to-r from-primary/10 via-secondary/10 to-accent/10 p-6 shadow-xl"
      >
        <div className="absolute inset-0 opacity-60" style={{ backgroundImage: 'radial-gradient(circle at 20% 20%, rgba(99,102,241,0.15), transparent 35%), radial-gradient(circle at 80% 10%, rgba(236,72,153,0.12), transparent 30%), radial-gradient(circle at 60% 80%, rgba(45,212,191,0.12), transparent 32%)' }} />
        <div className="relative space-y-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <p className="text-sm uppercase tracking-[0.2em] text-primary">Live Overview</p>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent animate-gradient">Dashboard</h1>
              <p className="text-muted-foreground text-lg">Monitor your AI research system</p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              <Badge variant="outline" className="bg-white/80 text-primary font-semibold border-primary/40 shadow-sm px-3 py-1">Auto-refresh</Badge>
              {latestSession?.id ? (
                <Badge variant="outline" className="bg-primary/10 text-primary font-semibold border-primary/40 shadow-sm px-3 py-1">
                  Latest: {latestSession.id.slice(0, 8)}
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-white/80 text-muted-foreground border-border px-3 py-1">No active session</Badge>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            {systemSignals.map((item) => (
              <Badge key={item.label} variant="outline" className="border-primary/30 bg-white/80 backdrop-blur px-3 py-1 shadow-sm">
                <span className="text-primary font-semibold mr-1">{item.value}</span>
                <span className="text-foreground/80">{item.label}</span>
              </Badge>
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            {stats.map((stat, index) => (
              <motion.div key={stat.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }}>
                <div className="glow-card rounded-xl p-5 shadow-sm hover:shadow-lg transition-all backdrop-blur border border-primary/15">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                      <p className="mt-1 text-3xl font-bold tracking-tight text-foreground">{stat.value}</p>
                      <p className="text-xs text-muted-foreground mt-1">{stat.change}</p>
                    </div>
                    <div className="rounded-xl bg-primary/10 p-3 text-primary shadow-inner">
                      <stat.icon className="h-6 w-6" />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Loading States */}
      {metricsLoading && <div className="text-center py-8 text-muted-foreground">Loading metrics...</div>}
      {metricsError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <p className="text-sm text-muted-foreground">Failed to load metrics</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetchMetrics()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Charts and Status */}
      <div className="grid gap-6 lg:grid-cols-7">
        <Card className="relative overflow-hidden lg:col-span-4">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/10 opacity-80" />
          <CardHeader className="relative z-10">
            <CardTitle>Research Metrics</CardTitle>
            <CardDescription>Latest session scores (higher is better)</CardDescription>
          </CardHeader>
          <CardContent className="relative z-10 space-y-4">
            <div className="space-y-3">
              {metricScores.map((item) => (
                <div key={item.label} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm font-medium">
                    <span>{item.label}</span>
                    <span className="text-muted-foreground">{Math.round(item.value)}%</span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${item.gradient}`}
                      style={{ width: `${Math.min(Math.max(item.value, 0), 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3">
              {taskStats.map((stat) => (
                <div key={stat.label} className="rounded-lg border bg-gradient-to-br from-card/80 via-card/60 to-primary/5 p-3 shadow-sm">
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="text-xl font-semibold tracking-tight">{stat.value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden lg:col-span-3">
          <div className="absolute inset-0 bg-gradient-to-br from-secondary/5 via-background to-accent/10 opacity-80" />
          <CardHeader className="relative z-10">
            <CardTitle>Agent Status</CardTitle>
            <CardDescription>Live agent activity</CardDescription>
          </CardHeader>
          <CardContent className="relative z-10">
            <div className="space-y-3">
              {agentList.map((agent) => {
                const Icon = statusIcon[ agent.status ];
                return (
                  <div key={agent.id} className="flex items-center justify-between rounded-lg border bg-card/70 p-3 hover:-translate-y-0.5 hover:shadow-md transition-all">
                    <div>
                      <p className="text-sm font-medium">{agent.name}</p>
                      {agent.currentTask && <p className="text-xs text-muted-foreground">{agent.currentTask}</p>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`h-2.5 w-2.5 rounded-full ${statusDot[ agent.status ]}`} />
                      <Badge variant={statusBadge[ agent.status ]} className="flex items-center gap-1">
                        <Icon className="h-3.5 w-3.5" />
                        <span className="capitalize">{agent.status}</span>
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Live pulse and highlights */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="relative overflow-hidden lg:col-span-2">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent/5 opacity-80" />
          <CardHeader className="relative z-10">
            <CardTitle>Live System Pulse</CardTitle>
            <CardDescription>Animated signals to fill the quiet space</CardDescription>
          </CardHeader>
          <CardContent className="relative z-10 space-y-4">
            {liveSignals.map((signal) => (
              <div key={signal.label} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm font-medium">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                    <span>{signal.label}</span>
                  </div>
                  <span className="text-muted-foreground">{signal.value}</span>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary/90 via-secondary/80 to-accent/80"
                    style={{ width: `${signal.intensity}%` }}
                  />
                  <div className="absolute inset-0 shimmer" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-secondary/5 via-background to-primary/5 opacity-80" />
          <CardHeader className="relative z-10">
            <CardTitle>Highlights</CardTitle>
            <CardDescription>Micro-interactions to fill whitespace</CardDescription>
          </CardHeader>
          <CardContent className="relative z-10 space-y-3">
            {[
              'Smooth hover lifts on cards and sessions',
              'Animated shimmer on live signals',
              'Gradient pills for system signals',
              'Backdrop blur across hero and tabs'
            ].map((item) => (
              <div key={item} className="flex items-center gap-2 rounded-lg border bg-card/70 p-3 hover:-translate-y-0.5 hover:shadow-md transition-all">
                <span className="h-2 w-2 rounded-full bg-secondary animate-pulse" />
                <p className="text-sm text-foreground/90">{item}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Sessions Tabs */}
      {!sessionsLoading && !sessionsError && sessions && sessions.length > 0 && (
        <Tabs defaultValue="sessions" className="space-y-4">
          <TabsList className="bg-card/60 backdrop-blur">
            <TabsTrigger value="sessions">Recent Sessions ({sessions.length})</TabsTrigger>
          </TabsList>
          <TabsContent value="sessions">
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-3">
                  {sessions.slice(0, 5).map((session) => (
                    <div key={session.id} className="flex items-center justify-between rounded-lg border bg-card/60 p-3 hover:-translate-y-0.5 hover:shadow-sm transition-all">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{session.config.topic.title}</p>
                        <p className="text-[11px] text-muted-foreground">{session.config.topic.domain} • {session.config.topic.complexity}</p>
                        <p className="text-[11px] text-muted-foreground">{session.id}</p>
                      </div>
                      <Badge variant={session.status === 'completed' ? 'default' : session.status === 'running' ? 'secondary' : 'outline'} className="capitalize">
                        {session.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {sessionsError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <p className="text-sm text-muted-foreground">Failed to load sessions</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetchSessions()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
