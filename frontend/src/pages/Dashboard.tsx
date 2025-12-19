import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity,
  FileText,
  TrendingUp,
  Users,
  CheckCircle2,
  Clock,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { MetricsChart } from '@/components/dashboard/MetricsChart';
import { AgentStatusCard } from '@/components/dashboard/AgentStatusCard';
import { RecentSessions } from '@/components/dashboard/RecentSessions';
import { motion } from 'framer-motion';
import { useOverallMetrics } from '@/hooks/useMetrics';
import { useResearchSessions } from '@/hooks/useResearchSessions';
import { parseApiError, getErrorMessage, getRecoveryAction } from '@/lib/errorHandler';
import type { ResearchSession } from '@/types';

// Helper to format time ago
function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// Transform session to activity format
function sessionToActivity(session: ResearchSession) {
  const statusIcon = {
    completed: CheckCircle2,
    running: Clock,
    failed: AlertCircle,
    configuring: Clock,
  };

  const statusText = {
    completed: `Research on ${session.config.topic.title} completed`,
    running: `${session.config.topic.title} in progress`,
    failed: `Research on ${session.config.topic.title} failed`,
    configuring: `Configuring ${session.config.topic.title}`,
  };

  return {
    id: session.id,
    title: statusText[ session.status ],
    time: formatTimeAgo(session.updatedAt),
    status: session.status === 'configuring' ? 'running' : session.status,
    icon: statusIcon[ session.status ],
  };
}

// Stats card skeleton for loading state
function StatsCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-16 mb-1" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

// Activity item skeleton for loading state
function ActivityItemSkeleton() {
  return (
    <div className="flex items-start gap-4 pb-4 border-b last:border-0">
      <Skeleton className="h-5 w-5 mt-1 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-20" />
      </div>
      <Skeleton className="h-5 w-16 rounded-full" />
    </div>
  );
}

export function Dashboard() {
  const {
    data: metrics,
    isLoading: metricsLoading,
    error: metricsError,
    refetch: refetchMetrics
  } = useOverallMetrics();

  const {
    data: sessions,
    isLoading: sessionsLoading,
    error: sessionsError,
    refetch: refetchSessions
  } = useResearchSessions();

  // Build stats array from real metrics data
  const stats = metrics ? [
    {
      title: 'Active Sessions',
      value: String(metrics.activeSessions),
      change: '+12%',
      icon: Activity,
      color: 'text-primary',
    },
    {
      title: 'Papers Generated',
      value: String(metrics.completedSessions),
      change: '+8%',
      icon: FileText,
      color: 'text-success',
    },
    {
      title: 'Avg Originality',
      value: `${Math.round(metrics.avgOriginalityScore)}%`,
      change: '+3%',
      icon: TrendingUp,
      color: 'text-accent',
    },
    {
      title: 'Active Agents',
      value: String(metrics.activeAgents),
      change: `+${metrics.totalAgents - metrics.activeAgents}`,
      icon: Users,
      color: 'text-secondary',
    },
  ] : [];

  // Transform sessions to activity format (most recent first, limit to 5)
  const recentActivity = sessions
    ? sessions
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, 5)
      .map(sessionToActivity)
    : [];

  // Error handling for metrics
  const metricsApiError = metricsError ? parseApiError(metricsError) : null;
  const metricsRecoveryAction = metricsApiError ? getRecoveryAction(metricsApiError) : null;

  // Error handling for sessions
  const sessionsApiError = sessionsError ? parseApiError(sessionsError) : null;
  const sessionsRecoveryAction = sessionsApiError ? getRecoveryAction(sessionsApiError) : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Monitor your AI research system performance and activities
        </p>
      </div>

      {/* Stats Cards Section */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metricsLoading ? (
          // Loading state with skeletons
          <>
            {[ 1, 2, 3, 4 ].map((i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <StatsCardSkeleton />
              </motion.div>
            ))}
          </>
        ) : metricsError ? (
          // Error state
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <AlertCircle className="h-8 w-8 text-destructive mb-2" />
              <p className="text-sm text-muted-foreground mb-4">
                {metricsApiError ? getErrorMessage(metricsApiError) : 'Failed to load metrics'}
              </p>
              {metricsRecoveryAction && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchMetrics()}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {metricsRecoveryAction.label}
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          // Data loaded successfully
          stats.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    <span className="text-success">{stat.change}</span> from last month
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-7">
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Research Metrics</CardTitle>
            <CardDescription>
              Originality and quality scores over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <MetricsChart />
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Agent Status</CardTitle>
            <CardDescription>
              Current agent activities and performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AgentStatusCard
              stages={sessions?.find(s => s.status === 'running')?.stages || sessions?.[ 0 ]?.stages}
              agents={sessions?.find(s => s.status === 'running')?.agents || sessions?.[ 0 ]?.agents}
              sessionStatus={sessions?.find(s => s.status === 'running')?.status || sessions?.[ 0 ]?.status}
            />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="activity" className="space-y-4">
        <TabsList>
          <TabsTrigger value="activity">Recent Activity</TabsTrigger>
          <TabsTrigger value="sessions">Active Sessions</TabsTrigger>
        </TabsList>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest updates from your research system</CardDescription>
            </CardHeader>
            <CardContent>
              {sessionsLoading ? (
                // Loading state with skeletons
                <div className="space-y-4">
                  {[ 1, 2, 3 ].map((i) => (
                    <ActivityItemSkeleton key={i} />
                  ))}
                </div>
              ) : sessionsError ? (
                // Error state
                <div className="flex flex-col items-center justify-center py-8">
                  <AlertCircle className="h-8 w-8 text-destructive mb-2" />
                  <p className="text-sm text-muted-foreground mb-4">
                    {sessionsApiError ? getErrorMessage(sessionsApiError) : 'Failed to load recent activity'}
                  </p>
                  {sessionsRecoveryAction && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => refetchSessions()}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      {sessionsRecoveryAction.label}
                    </Button>
                  )}
                </div>
              ) : recentActivity.length === 0 ? (
                // Empty state
                <div className="flex flex-col items-center justify-center py-8">
                  <Activity className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">
                    No recent activity. Start a new research session to see updates here.
                  </p>
                </div>
              ) : (
                // Data loaded successfully
                <div className="space-y-4">
                  {recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-start gap-4 pb-4 last:pb-0 border-b last:border-0">
                      <div className={`mt-1 ${activity.status === 'completed' ? 'text-success' :
                        activity.status === 'running' ? 'text-primary' :
                          'text-warning'
                        }`}>
                        <activity.icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium">{activity.title}</p>
                        <p className="text-xs text-muted-foreground">{activity.time}</p>
                      </div>
                      <Badge variant={
                        activity.status === 'completed' ? 'default' :
                          activity.status === 'running' ? 'secondary' :
                            'outline'
                      }>
                        {activity.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sessions">
          <RecentSessions />
        </TabsContent>
      </Tabs>
    </div>
  );
}
