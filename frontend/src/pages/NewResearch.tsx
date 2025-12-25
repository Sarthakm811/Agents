import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Sparkles, X, Loader2 } from 'lucide-react';
import { useCreateSession, useStartSession } from '@/hooks/useResearchSessions';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

export function NewResearch() {
  const navigate = useNavigate();
  const { mutate: createSession, isPending: isCreating } = useCreateSession();
  const { mutate: startSession, isPending: isStarting } = useStartSession();
  const isPending = isCreating || isStarting;

  const [ formData, setFormData ] = useState({
    title: '',
    domain: '',
    complexity: 'intermediate' as 'basic' | 'intermediate' | 'advanced',
    authorName: '',
    authorInstitution: '',
    keywords: [] as string[],
    keywordInput: '',
  });

  const handleAddKeyword = () => {
    if (formData.keywordInput.trim() && !formData.keywords.includes(formData.keywordInput.trim())) {
      setFormData({
        ...formData,
        keywords: [ ...formData.keywords, formData.keywordInput.trim() ],
        keywordInput: '',
      });
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((k) => k !== keyword),
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    createSession(
      {
        topic: {
          title: formData.title,
          domain: formData.domain,
          keywords: formData.keywords,
          complexity: formData.complexity,
        },
        authorName: formData.authorName,
        authorInstitution: formData.authorInstitution,
      },
      {
        onSuccess: (session) => {
          toast.success('Research session created! Starting research...');
          // Automatically start the session after creation
          startSession(session.id, {
            onSuccess: () => {
              toast.success('Research started successfully!');
              navigate('/sessions');
            },
            onError: (error) => {
              toast.error(`Failed to start session: ${error.message}`);
              navigate('/sessions');
            },
          });
        },
        onError: (error) => {
          toast.error(`Failed to create session: ${error.message}`);
        },
      }
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="h-8 w-8 text-primary" />
          New Research Project
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure your AI-powered research session
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <Card className="hover-lift gradient-card border-2">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl">Research Configuration</CardTitle>
            <CardDescription className="text-base">
              Provide details about your research topic and parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Research Title *</Label>
                  <Input
                    id="title"
                    placeholder="e.g., Quantum Computing Applications in Machine Learning"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="domain">Research Domain *</Label>
                    <Input
                      id="domain"
                      placeholder="e.g., Computer Science, AI Ethics"
                      value={formData.domain}
                      onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="complexity">Complexity Level *</Label>
                    <Select
                      value={formData.complexity}
                      onValueChange={(value: 'basic' | 'intermediate' | 'advanced') =>
                        setFormData({ ...formData, complexity: value })
                      }
                    >
                      <SelectTrigger id="complexity">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="basic">Basic</SelectItem>
                        <SelectItem value="intermediate">Intermediate</SelectItem>
                        <SelectItem value="advanced">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="keywords">Keywords</Label>
                  <div className="flex gap-2">
                    <Input
                      id="keywords"
                      placeholder="Add keywords (press Enter)"
                      value={formData.keywordInput}
                      onChange={(e) => setFormData({ ...formData, keywordInput: e.target.value })}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddKeyword();
                        }
                      }}
                    />
                    <Button type="button" onClick={handleAddKeyword} variant="secondary">
                      Add
                    </Button>
                  </div>
                  {formData.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {formData.keywords.map((keyword) => (
                        <Badge key={keyword} variant="secondary">
                          {keyword}
                          <button
                            type="button"
                            onClick={() => handleRemoveKeyword(keyword)}
                            className="ml-2 hover:text-destructive"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="authorName">Author Name *</Label>
                    <Input
                      id="authorName"
                      placeholder="e.g., Dr. Jane Smith"
                      value={formData.authorName}
                      onChange={(e) => setFormData({ ...formData, authorName: e.target.value })}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="authorInstitution">Institution *</Label>
                    <Input
                      id="authorInstitution"
                      placeholder="e.g., MIT, Stanford University"
                      value={formData.authorInstitution}
                      onChange={(e) => setFormData({ ...formData, authorInstitution: e.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-4 justify-end pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => navigate('/')} disabled={isPending}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isPending}>
                  {isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Start Research
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <Card className="gradient-bg">
          <CardHeader>
            <CardTitle>What happens next?</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold">
                  1
                </div>
                <h4 className="font-semibold">Literature Review</h4>
                <p className="text-sm text-muted-foreground">
                  AI agents will search and analyze relevant academic papers
                </p>
              </div>
              <div className="space-y-2">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold">
                  2
                </div>
                <h4 className="font-semibold">Research Execution</h4>
                <p className="text-sm text-muted-foreground">
                  Automated hypothesis generation, methodology design, and analysis
                </p>
              </div>
              <div className="space-y-2">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold">
                  3
                </div>
                <h4 className="font-semibold">Paper Generation</h4>
                <p className="text-sm text-muted-foreground">
                  Complete paper composition with originality and ethics verification
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}