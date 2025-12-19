import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Download, FileText, ExternalLink, AlertCircle, Loader2 } from 'lucide-react';
import { useCompletedSessions, useDownloadPaper, useSessionResults } from '@/hooks/useResults';
import { toast } from 'sonner';
import type { ResearchSession } from '@/types';

function getScoreBadge(score: number): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } {
  if (score >= 90) return { label: 'Excellent', variant: 'secondary' };
  if (score >= 75) return { label: 'Good', variant: 'secondary' };
  if (score >= 60) return { label: 'Fair', variant: 'outline' };
  return { label: 'Needs Review', variant: 'destructive' };
}

function ResultCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
          <Skeleton className="h-8 w-8" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            {[ 1, 2, 3 ].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-20" />
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 pt-4 border-t">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-36" />
            <Skeleton className="h-10 w-36" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


interface ResultCardProps {
  session: ResearchSession;
  onViewReport: (sessionId: string) => void;
  onDownload: (sessionId: string, format: 'pdf' | 'latex') => void;
  isDownloading: boolean;
  downloadingFormat: 'pdf' | 'latex' | null;
}

function ResultCard({ session, onViewReport, onDownload, isDownloading, downloadingFormat }: ResultCardProps) {
  const { metrics, config, createdAt } = session;
  const formattedDate = new Date(createdAt).toLocaleDateString();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-xl">{config.topic.title}</CardTitle>
            <CardDescription>
              By {config.authorName} • {formattedDate}
            </CardDescription>
          </div>
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Originality Score</p>
              <div className="flex items-center gap-2">
                <div className="text-2xl font-bold">{metrics.originalityScore}%</div>
                <Badge variant={getScoreBadge(metrics.originalityScore).variant}>
                  {getScoreBadge(metrics.originalityScore).label}
                </Badge>
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Novelty Score</p>
              <div className="flex items-center gap-2">
                <div className="text-2xl font-bold">{metrics.noveltyScore}%</div>
                <Badge variant={getScoreBadge(metrics.noveltyScore).variant}>
                  {getScoreBadge(metrics.noveltyScore).label}
                </Badge>
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Ethics Compliance</p>
              <div className="flex items-center gap-2">
                <div className="text-2xl font-bold">{metrics.ethicsScore}%</div>
                <Badge variant={getScoreBadge(metrics.ethicsScore).variant}>
                  {getScoreBadge(metrics.ethicsScore).label}
                </Badge>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-4 border-t">
            <Button
              onClick={() => onDownload(session.id, 'pdf')}
              disabled={isDownloading}
            >
              {isDownloading && downloadingFormat === 'pdf' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Download PDF
            </Button>
            <Button
              variant="outline"
              onClick={() => onDownload(session.id, 'latex')}
              disabled={isDownloading}
            >
              {isDownloading && downloadingFormat === 'latex' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Download LaTeX
            </Button>
            <Button variant="outline" onClick={() => onViewReport(session.id)}>
              <ExternalLink className="h-4 w-4 mr-2" />
              View Full Report
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


interface ReportDialogProps {
  sessionId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ReportDialog({ sessionId, open, onOpenChange }: ReportDialogProps) {
  const { data: results, isLoading, error } = useSessionResults(sessionId || '');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Research Report</DialogTitle>
          <DialogDescription>
            Full details of the completed research session
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>Failed to load report details</span>
          </div>
        )}

        {results && (
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-lg">{results.title}</h3>
              <p className="text-sm text-muted-foreground">
                By {results.author} • {results.institution}
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">{results.originalityScore}%</div>
                <div className="text-sm text-muted-foreground">Originality</div>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">{results.noveltyScore}%</div>
                <div className="text-sm text-muted-foreground">Novelty</div>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">{results.ethicsScore}%</div>
                <div className="text-sm text-muted-foreground">Ethics</div>
              </div>
            </div>

            {results.paper && (
              <>
                <div>
                  <h4 className="font-semibold mb-2">Abstract</h4>
                  <p className="text-sm text-muted-foreground">{results.paper.abstract}</p>
                </div>

                <div className="flex gap-4 text-sm text-muted-foreground">
                  <span>{results.paper.pages} pages</span>
                  <span>{results.paper.citations} citations</span>
                </div>

                {results.paper.sections && results.paper.sections.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Sections</h4>
                    <ul className="space-y-1">
                      {results.paper.sections.map((section, index) => (
                        <li key={index} className="text-sm text-muted-foreground">
                          • {section.title}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}


export function Results() {
  const { data: sessions, isLoading, error, refetch } = useCompletedSessions();
  const downloadMutation = useDownloadPaper();
  const [ selectedSessionId, setSelectedSessionId ] = useState<string | null>(null);
  const [ reportDialogOpen, setReportDialogOpen ] = useState(false);
  const [ downloadingSessionId, setDownloadingSessionId ] = useState<string | null>(null);
  const [ downloadingFormat, setDownloadingFormat ] = useState<'pdf' | 'latex' | null>(null);

  const handleDownload = async (sessionId: string, format: 'pdf' | 'latex') => {
    setDownloadingSessionId(sessionId);
    setDownloadingFormat(format);

    downloadMutation.mutate(
      { sessionId, format },
      {
        onSuccess: () => {
          toast.success(`Paper downloaded successfully as ${format.toUpperCase()}`);
          setDownloadingSessionId(null);
          setDownloadingFormat(null);
        },
        onError: (err) => {
          toast.error(`Failed to download paper: ${err.message}`);
          setDownloadingSessionId(null);
          setDownloadingFormat(null);
        },
      }
    );
  };

  const handleViewReport = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setReportDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Research Results</h1>
        <p className="text-muted-foreground mt-1">
          View and download completed research papers
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid gap-6">
          {[ 1, 2, 3 ].map((i) => (
            <ResultCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to load results</h3>
            <p className="text-muted-foreground mb-4">
              {error instanceof Error ? error.message : 'An unexpected error occurred'}
            </p>
            <Button onClick={() => refetch()}>Try Again</Button>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && sessions && sessions.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No completed research yet</h3>
            <p className="text-muted-foreground text-center max-w-md">
              Once your research sessions are completed, they will appear here.
              Start a new research session to generate your first paper.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Results List */}
      {!isLoading && !error && sessions && sessions.length > 0 && (
        <div className="grid gap-6">
          {sessions.map((session) => (
            <ResultCard
              key={session.id}
              session={session}
              onViewReport={handleViewReport}
              onDownload={handleDownload}
              isDownloading={downloadingSessionId === session.id}
              downloadingFormat={downloadingSessionId === session.id ? downloadingFormat : null}
            />
          ))}
        </div>
      )}

      {/* Report Dialog */}
      <ReportDialog
        sessionId={selectedSessionId}
        open={reportDialogOpen}
        onOpenChange={setReportDialogOpen}
      />
    </div>
  );
}
