import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { CheckCircle2, AlertTriangle, Info, AlertCircle, RefreshCw, ShieldCheck } from 'lucide-react';
import { useAllComplianceReports } from '@/hooks/useCompliance';
import { parseApiError, getErrorMessage, getRecoveryAction } from '@/lib/errorHandler';
import type { ComplianceReport, ComplianceCategory } from '@/types';

// Skeleton for compliance category card
function ComplianceCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-4 w-20 mt-1" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-2 w-full" />
          <div className="space-y-2 pt-2">
            {[ 1, 2, 3 ].map((i) => (
              <div key={i} className="flex items-center gap-2">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-4 w-32" />
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Skeleton for audit item
function AuditItemSkeleton() {
  return (
    <div className="flex items-center justify-between pb-4 border-b last:border-0">
      <div className="space-y-2">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right space-y-1">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-6 w-12" />
        </div>
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
    </div>
  );
}


// Aggregate compliance categories from all reports
function aggregateCategories(reports: ComplianceReport[]): ComplianceCategory[] {
  if (!reports || reports.length === 0) return [];

  // Group categories by name and calculate average scores
  const categoryMap = new Map<string, { totalScore: number; count: number; checks: Map<string, { passed: number; warning: number; failed: number }> }>();

  reports.forEach((report) => {
    report.categories.forEach((category) => {
      const existing = categoryMap.get(category.name);
      if (existing) {
        existing.totalScore += category.score;
        existing.count += 1;
        category.checks.forEach((check) => {
          const checkStats = existing.checks.get(check.name) || { passed: 0, warning: 0, failed: 0 };
          checkStats[ check.status ] += 1;
          existing.checks.set(check.name, checkStats);
        });
      } else {
        const checksMap = new Map<string, { passed: number; warning: number; failed: number }>();
        category.checks.forEach((check) => {
          checksMap.set(check.name, { passed: 0, warning: 0, failed: 0, [ check.status ]: 1 });
        });
        categoryMap.set(category.name, {
          totalScore: category.score,
          count: 1,
          checks: checksMap,
        });
      }
    });
  });

  // Convert to array format
  return Array.from(categoryMap.entries()).map(([ name, data ]) => {
    const avgScore = Math.round(data.totalScore / data.count);
    const checks = Array.from(data.checks.entries()).map(([ checkName, stats ]) => {
      // Determine overall status based on majority
      let status: 'passed' | 'failed' | 'warning' = 'passed';
      if (stats.failed > 0) status = 'failed';
      else if (stats.warning > stats.passed) status = 'warning';
      return { name: checkName, status };
    });

    return {
      name,
      score: avgScore,
      status: avgScore >= 90 ? 'passed' : avgScore >= 70 ? 'warning' : 'failed',
      checks,
    } as ComplianceCategory;
  });
}

// Transform reports to audit format
function reportsToAudits(reports: ComplianceReport[]) {
  return reports.map((report) => ({
    id: report.sessionId,
    session: `Session ${report.sessionId.slice(0, 8)}`,
    date: new Date().toISOString().split('T')[ 0 ], // Use current date as placeholder
    status: report.complianceScore >= 90 ? 'approved' : report.complianceScore >= 70 ? 'review' : 'failed',
    score: report.complianceScore,
  }));
}

export function Ethics() {
  const {
    data: complianceReports,
    isLoading,
    error,
    refetch,
  } = useAllComplianceReports();

  // Error handling
  const apiError = error ? parseApiError(error) : null;
  const recoveryAction = apiError ? getRecoveryAction(apiError) : null;

  // Aggregate categories from all reports
  const aggregatedCategories = complianceReports ? aggregateCategories(complianceReports) : [];

  // Transform reports to audits
  const recentAudits = complianceReports ? reportsToAudits(complianceReports) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Ethics & Compliance</h1>
        <p className="text-muted-foreground mt-1">
          Monitor ethical compliance and governance across all research activities
        </p>
      </div>

      {/* Compliance Categories Section */}
      <div className="grid gap-6 md:grid-cols-3">
        {isLoading ? (
          // Loading state with skeletons
          <>
            {[ 1, 2, 3 ].map((i) => (
              <ComplianceCardSkeleton key={i} />
            ))}
          </>
        ) : error ? (
          // Error state
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <AlertCircle className="h-8 w-8 text-destructive mb-2" />
              <p className="text-sm text-muted-foreground mb-4">
                {apiError ? getErrorMessage(apiError) : 'Failed to load compliance data'}
              </p>
              {recoveryAction && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {recoveryAction.label}
                </Button>
              )}
            </CardContent>
          </Card>
        ) : aggregatedCategories.length === 0 ? (
          // Empty state
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <ShieldCheck className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm font-medium mb-1">No Ethics Audits Available</p>
              <p className="text-sm text-muted-foreground text-center">
                Complete a research session to see ethics and compliance assessments here.
              </p>
            </CardContent>
          </Card>
        ) : (
          // Data loaded successfully
          aggregatedCategories.map((category) => (
            <Card key={category.name}>
              <CardHeader>
                <CardTitle className="text-base">{category.name}</CardTitle>
                <CardDescription>Compliance Score</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="text-3xl font-bold">{category.score}%</div>
                    <Badge variant={category.status === 'passed' ? 'secondary' : 'outline'}>
                      {category.status}
                    </Badge>
                  </div>
                  <Progress value={category.score} className="h-2" />

                  <div className="space-y-2 pt-2">
                    {category.checks.map((check) => (
                      <div key={check.name} className="flex items-center gap-2 text-sm">
                        {check.status === 'passed' ? (
                          <CheckCircle2 className="h-4 w-4 text-success" />
                        ) : check.status === 'warning' ? (
                          <AlertTriangle className="h-4 w-4 text-warning" />
                        ) : (
                          <Info className="h-4 w-4 text-info" />
                        )}
                        <span className="text-muted-foreground">{check.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>


      {/* Recent Audits Section */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Ethics Audits</CardTitle>
          <CardDescription>
            Compliance reviews for completed research sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            // Loading state with skeletons
            <div className="space-y-4">
              {[ 1, 2, 3 ].map((i) => (
                <AuditItemSkeleton key={i} />
              ))}
            </div>
          ) : error ? (
            // Error state
            <div className="flex flex-col items-center justify-center py-8">
              <AlertCircle className="h-8 w-8 text-destructive mb-2" />
              <p className="text-sm text-muted-foreground mb-4">
                {apiError ? getErrorMessage(apiError) : 'Failed to load audit data'}
              </p>
              {recoveryAction && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {recoveryAction.label}
                </Button>
              )}
            </div>
          ) : recentAudits.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center py-8">
              <ShieldCheck className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">
                No ethics audits available. Complete a research session to see compliance reviews here.
              </p>
            </div>
          ) : (
            // Data loaded successfully
            <div className="space-y-4">
              {recentAudits.map((audit) => (
                <div key={audit.id} className="flex items-center justify-between pb-4 last:pb-0 border-b last:border-0">
                  <div className="space-y-1">
                    <p className="font-medium">{audit.session}</p>
                    <p className="text-sm text-muted-foreground">{audit.date}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Compliance Score</p>
                      <p className="text-lg font-semibold">{audit.score}%</p>
                    </div>
                    <Badge variant={audit.status === 'approved' ? 'secondary' : 'outline'}>
                      {audit.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
