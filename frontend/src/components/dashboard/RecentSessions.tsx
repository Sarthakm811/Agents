import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Eye } from 'lucide-react';

const sessions = [
  {
    id: 1,
    title: 'Quantum Computing Applications in AI',
    domain: 'Computer Science',
    progress: 85,
    status: 'running',
    author: 'Dr. Smith',
  },
  {
    id: 2,
    title: 'Ethical Implications of AGI',
    domain: 'AI Ethics',
    progress: 100,
    status: 'completed',
    author: 'Prof. Johnson',
  },
  {
    id: 3,
    title: 'Neural Architecture Search Optimization',
    domain: 'Machine Learning',
    progress: 45,
    status: 'running',
    author: 'Dr. Chen',
  },
];

export function RecentSessions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Research Sessions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {sessions.map((session) => (
            <div key={session.id} className="space-y-3 pb-6 last:pb-0 border-b last:border-0">
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <h4 className="text-sm font-semibold">{session.title}</h4>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{session.domain}</span>
                    <span>•</span>
                    <span>{session.author}</span>
                  </div>
                </div>
                <Badge variant={session.status === 'completed' ? 'secondary' : 'default'}>
                  {session.status}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">{session.progress}%</span>
                </div>
                <Progress value={session.progress} className="h-2" />
              </div>
              
              <Button variant="outline" size="sm" className="w-full">
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}