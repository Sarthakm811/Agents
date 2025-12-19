import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Eye, Pause, Play, StopCircle } from 'lucide-react';
import { useResearchSessions, useStartSession, usePauseSession, useStopSession } from '@/hooks/useResearchSessions';
import { toast } from 'sonner';

// Removed static mock data; sessions will be fetched from the backend.

export function Sessions() {
  const { data: sessions, isLoading, isError } = useResearchSessions();
  const startMutation = useStartSession();
  const pauseMutation = usePauseSession();
  const stopMutation = useStopSession();

  const handleAction = (action: 'start' | 'pause' | 'stop', sessionId: string) => {
    const mutationMap = {
      start: startMutation,
      pause: pauseMutation,
      stop: stopMutation,
    } as const;
    const mutation = mutationMap[ action ];
    mutation.mutate(sessionId, {
      onSuccess: () => toast.success(`${action.charAt(0).toUpperCase() + action.slice(1)}ed session`),
      onError: (e: any) => toast.error(e.message ?? 'Action failed'),
    });
  };

  if (isLoading) return <div>Loading sessions...</div>;
  if (isError) return <div>Error loading sessions.</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Research Sessions</h1>
        <p className="text-muted-foreground mt-1">
          Manage and monitor your active and completed research sessions
        </p>
      </div>

      <Tabs defaultValue="active" className="space-y-4">
        <TabsList>
          <TabsTrigger value="active">Active Sessions</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="all">All Sessions</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Research Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Domain</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Current Stage</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions
                    ?.filter((s) => s.status === 'running' || s.status === 'configuring')
                    .map((session) => (
                      <TableRow key={session.id}>
                        <TableCell className="font-medium">{session.config.topic.title}</TableCell>
                        <TableCell>{session.config.topic.domain}</TableCell>
                        <TableCell>{session.config.authorName}</TableCell>
                        <TableCell>{session.stages.find(st => st.status === 'running')?.name ?? 'N/A'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress
                              value={session.stages ? (session.stages.filter(s => s.status === 'completed').length / session.stages.length) * 100 : 0}
                              className="w-20 h-2"
                            />
                            <span className="text-xs text-muted-foreground">
                              {session.stages ? Math.round((session.stages.filter(s => s.status === 'completed').length / session.stages.length) * 100) : 0}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge>{session.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="icon" onClick={() => {/* view details */ }}>
                              <Eye className="h-4 w-4" />
                            </Button>
                            {session.status === 'configuring' && (
                              <Button variant="ghost" size="icon" onClick={() => handleAction('start', session.id)} title="Start Research">
                                <Play className="h-4 w-4" />
                              </Button>
                            )}
                            {session.status === 'running' && (
                              <Button variant="ghost" size="icon" onClick={() => handleAction('pause', session.id)}>
                                <Pause className="h-4 w-4" />
                              </Button>
                            )}
                            <Button variant="ghost" size="icon" onClick={() => handleAction('stop', session.id)}>
                              <StopCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardHeader>
              <CardTitle>Completed Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Domain</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Completed Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions
                    ?.filter((s) => s.status === 'completed')
                    .map((session) => (
                      <TableRow key={session.id}>
                        <TableCell className="font-medium">{session.config.topic.title}</TableCell>
                        <TableCell>{session.config.topic.domain}</TableCell>
                        <TableCell>{session.config.authorName}</TableCell>
                        <TableCell>{new Date(session.updatedAt).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">{session.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="all">
          <Card>
            <CardHeader>
              <CardTitle>All Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Domain</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions?.map((session) => (
                    <TableRow key={session.id}>
                      <TableCell className="font-medium">{session.config.topic.title}</TableCell>
                      <TableCell>{session.config.topic.domain}</TableCell>
                      <TableCell>{session.config.authorName}</TableCell>
                      <TableCell>{new Date(session.createdAt).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress
                            value={session.status === 'completed' ? 100 :
                              session.stages ? (session.stages.filter(s => s.status === 'completed').length / session.stages.length) * 100 : 0}
                            className="w-20 h-2"
                          />
                          <span className="text-xs text-muted-foreground">
                            {session.status === 'completed' ? 100 :
                              session.stages ? Math.round((session.stages.filter(s => s.status === 'completed').length / session.stages.length) * 100) : 0}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={session.status === 'completed' ? 'secondary' : 'default'}>
                          {session.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                          {session.status === 'configuring' && (
                            <Button variant="ghost" size="icon" onClick={() => handleAction('start', session.id)} title="Start Research">
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}