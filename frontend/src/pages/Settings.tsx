import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw, Loader2, Sliders } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { useSettings, useUpdateSettings } from '@/hooks/useSettings';
import { parseApiError, getErrorMessage, getRecoveryAction } from '@/lib/errorHandler';
import type { UserSettings, UserPreferences } from '@/types';

// Form field skeleton for loading state
function FormFieldSkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

// Switch field skeleton for loading state
function SwitchFieldSkeleton() {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-64" />
      </div>
      <Skeleton className="h-6 w-11 rounded-full" />
    </div>
  );
}

export function Settings() {
  const { data: settings, isLoading, error, refetch } = useSettings();
  const updateSettings = useUpdateSettings();

  // Local form state
  const [ formData, setFormData ] = useState<UserSettings>({
    fullName: '',
    email: '',
    institution: '',
    preferences: {
      autoStartEthicsReview: true,
      enablePlagiarismDetection: true,
      realTimeNotifications: true,
    },
  });

  // Track if form has been modified
  const [ isDirty, setIsDirty ] = useState(false);

  // Populate form when settings are loaded
  useEffect(() => {
    if (settings) {
      setFormData(settings);
      setIsDirty(false);
    }
  }, [ settings ]);

  // Handle text input changes
  const handleInputChange = (field: keyof Omit<UserSettings, 'preferences'>) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [ field ]: e.target.value,
    }));
    setIsDirty(true);
  };

  // Handle preference toggle changes
  const handlePreferenceChange = (field: keyof UserPreferences) => (checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [ field ]: checked,
      },
    }));
    setIsDirty(true);
  };

  // Handle cancel - reset form to original settings
  const handleCancel = () => {
    if (settings) {
      setFormData(settings);
      setIsDirty(false);
    }
  };

  // Handle save
  const handleSave = () => {
    updateSettings.mutate(formData, {
      onSuccess: () => {
        toast.success('Settings saved successfully');
        setIsDirty(false);
      },
      onError: (err) => {
        const apiError = parseApiError(err);
        toast.error(getErrorMessage(apiError));
        // Form state is preserved on error (no reset)
      },
    });
  };

  // Error handling
  const apiError = error ? parseApiError(error) : null;
  const recoveryAction = apiError ? getRecoveryAction(apiError) : null;

  return (
    <div className="space-y-6 p-6 relative">
      {/* Gradient Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-20 right-10 w-72 h-72 bg-accent/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-40 left-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-3 relative max-w-4xl"
      >
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20">
            <Sliders className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent animate-gradient">Settings</h1>
            <p className="text-muted-foreground text-lg">Configure your research system preferences</p>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-4xl"
      >
        <Card className="glow-card">
          <CardHeader>
            <CardTitle className="text-2xl">General Settings</CardTitle>
            <CardDescription>Manage your account and system preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {error ? (
              // Error state
              <div className="flex flex-col items-center justify-center py-8">
                <AlertCircle className="h-8 w-8 text-destructive mb-2" />
                <p className="text-sm text-muted-foreground mb-4">
                  {apiError ? getErrorMessage(apiError) : 'Failed to load settings'}
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
            ) : (
              <>
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    {isLoading ? (
                      <>
                        <FormFieldSkeleton />
                        <FormFieldSkeleton />
                      </>
                    ) : (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="name">Full Name</Label>
                          <Input
                            id="name"
                            value={formData.fullName}
                            onChange={handleInputChange('fullName')}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            value={formData.email}
                            onChange={handleInputChange('email')}
                          />
                        </div>
                      </>
                    )}
                  </div>

                  {isLoading ? (
                    <FormFieldSkeleton />
                  ) : (
                    <div className="space-y-2">
                      <Label htmlFor="institution">Institution</Label>
                      <Input
                        id="institution"
                        value={formData.institution}
                        onChange={handleInputChange('institution')}
                      />
                    </div>
                  )}
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Research Preferences</h3>

                  {isLoading ? (
                    <>
                      <SwitchFieldSkeleton />
                      <SwitchFieldSkeleton />
                      <SwitchFieldSkeleton />
                    </>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Auto-start Ethics Review</Label>
                          <p className="text-sm text-muted-foreground">
                            Automatically run ethics compliance checks after paper generation
                          </p>
                        </div>
                        <Switch
                          checked={formData.preferences.autoStartEthicsReview}
                          onCheckedChange={handlePreferenceChange('autoStartEthicsReview')}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Enable Plagiarism Detection</Label>
                          <p className="text-sm text-muted-foreground">
                            Check all generated content for originality
                          </p>
                        </div>
                        <Switch
                          checked={formData.preferences.enablePlagiarismDetection}
                          onCheckedChange={handlePreferenceChange('enablePlagiarismDetection')}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Real-time Notifications</Label>
                          <p className="text-sm text-muted-foreground">
                            Receive updates about research progress
                          </p>
                        </div>
                        <Switch
                          checked={formData.preferences.realTimeNotifications}
                          onCheckedChange={handlePreferenceChange('realTimeNotifications')}
                        />
                      </div>
                    </>
                  )}
                </div>

                <Separator />

                <div className="flex justify-end gap-4">
                  {isLoading ? (
                    <>
                      <Skeleton className="h-10 w-20" />
                      <Skeleton className="h-10 w-28" />
                    </>
                  ) : (
                    <>
                      <Button
                        variant="outline"
                        onClick={handleCancel}
                        disabled={!isDirty || updateSettings.isPending}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSave}
                        disabled={!isDirty || updateSettings.isPending}
                      >
                        {updateSettings.isPending ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          'Save Changes'
                        )}
                      </Button>
                    </>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
