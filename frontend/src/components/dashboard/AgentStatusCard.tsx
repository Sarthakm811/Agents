import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
  tasksCompleted: number;
}

interface Stage {
  id: string;
  name: string;
  status: string;
  progress: number;
}

interface AgentStatusCardProps {
  agents?: Agent[];
  stages?: Stage[];
  sessionStatus?: string;
}

// Map stages to agent names for display
const stageToAgentMap: Record<string, string> = {
  'Literature Review': 'Literature Agent',
  'Hypothesis Generation': 'Hypothesis Agent',
  'Methodology Design': 'Methodology Agent',
  'Data Analysis': 'Data Agent',
  'Paper Composition': 'Writing Agent',
  'Ethics Review': 'Ethics Agent',
};

export function AgentStatusCard({ agents, stages, sessionStatus }: AgentStatusCardProps) {
  // If we have stages data, use it to show real progress
  if (stages && stages.length > 0) {
    return (
      <div className="space-y-4">
        {stages.map((stage) => {
          const agentName = stageToAgentMap[ stage.name ] || stage.name;
          const status = stage.status === 'completed' ? 'completed' :
            stage.status === 'running' ? 'working' : 'pending';

          return (
            <div key={stage.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium">{agentName}</p>
                  <p className="text-xs text-muted-foreground">
                    {stage.name}
                  </p>
                </div>
                <Badge
                  variant={
                    status === 'working' ? 'default' :
                      status === 'completed' ? 'secondary' :
                        'outline'
                  }
                >
                  {status}
                </Badge>
              </div>
              <Progress value={stage.progress} className="h-2" />
            </div>
          );
        })}
      </div>
    );
  }

  // Fallback to agents data or default display
  const displayAgents = agents || [
    { id: '1', name: 'Literature Agent', type: 'research', status: 'idle', tasksCompleted: 0 },
    { id: '2', name: 'Hypothesis Agent', type: 'analysis', status: 'idle', tasksCompleted: 0 },
    { id: '3', name: 'Methodology Agent', type: 'design', status: 'idle', tasksCompleted: 0 },
    { id: '4', name: 'Writing Agent', type: 'composition', status: 'idle', tasksCompleted: 0 },
    { id: '5', name: 'Ethics Agent', type: 'governance', status: 'idle', tasksCompleted: 0 },
  ];

  return (
    <div className="space-y-4">
      {displayAgents.map((agent) => (
        <div key={agent.id} className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium">{agent.name}</p>
              <p className="text-xs text-muted-foreground">
                {agent.tasksCompleted} tasks completed
              </p>
            </div>
            <Badge
              variant={
                agent.status === 'working' ? 'default' :
                  agent.status === 'completed' ? 'secondary' :
                    'outline'
              }
            >
              {agent.status}
            </Badge>
          </div>
          <Progress
            value={agent.status === 'completed' ? 100 : agent.status === 'working' ? 50 : 0}
            className="h-2"
          />
        </div>
      ))}
    </div>
  );
}