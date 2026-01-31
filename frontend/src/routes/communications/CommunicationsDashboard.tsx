// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E11: Change Communications Dashboard
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  MessageSquare,
  Mail,
  FileText,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  BookOpen,
} from 'lucide-react';
import { api } from '@/lib/api/client';
import {
  ENDPOINTS,
  type ChangeRecord,
  type Communication,
  type CommunicationTemplate,
  type ChangeDashboardData,
} from './contracts';

// Stat Card Component
function StatCard({
  icon: Icon,
  label,
  value,
  subtext,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  subtext?: string;
  color: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtext && <p className="text-xs text-gray-400">{subtext}</p>}
        </div>
      </div>
    </div>
  );
}

// Change Card Component
function ChangeCard({ change }: { change: ChangeRecord }) {
  const stateColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    submitted: 'bg-blue-100 text-blue-800',
    peer_review: 'bg-purple-100 text-purple-800',
    cab_review: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    scheduled: 'bg-indigo-100 text-indigo-800',
    in_progress: 'bg-orange-100 text-orange-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-gray-100 text-gray-800',
    failed: 'bg-red-100 text-red-800',
  };

  const priorityColors: Record<string, string> = {
    critical: 'text-red-600',
    high: 'text-orange-600',
    medium: 'text-yellow-600',
    low: 'text-green-600',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-blue-600">{change.change_number}</span>
            <span className={`px-2 py-0.5 rounded-full text-xs ${stateColors[change.state]}`}>
              {change.state.replace('_', ' ')}
            </span>
          </div>
          <h4 className="font-medium mt-1">{change.title}</h4>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{change.description}</p>
        </div>
        <span className={`text-sm font-medium ${priorityColors[change.priority]}`}>
          {change.priority.toUpperCase()}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Send className="h-3 w-3" />
          {change.communications_sent} sent
        </span>
        <span className="flex items-center gap-1">
          <BookOpen className="h-3 w-3" />
          {change.kb_articles_linked} KB articles
        </span>
        {change.planned_start && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(change.planned_start).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}

// Template Card Component
function TemplateCard({
  template,
  onPreview,
}: {
  template: CommunicationTemplate;
  onPreview: (id: string) => void;
}) {
  const channelIcons: Record<string, React.ElementType> = {
    email: Mail,
    teams: MessageSquare,
    slack: MessageSquare,
    servicenow: FileText,
  };

  const Icon = channelIcons[template.channel] || MessageSquare;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon className="h-5 w-5 text-blue-500" />
          <div>
            <h4 className="font-medium">{template.name}</h4>
            <p className="text-xs text-gray-500">{template.template_type.replace('_', ' ')}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {template.is_default && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">Default</span>
          )}
          <button
            onClick={() => onPreview(template.id)}
            className="text-sm text-blue-600 hover:underline"
          >
            Preview
          </button>
        </div>
      </div>
      <p className="text-sm text-gray-500 mt-2 line-clamp-2">{template.description}</p>
      <div className="mt-2 text-xs text-gray-400">Used {template.usage_count} times</div>
    </div>
  );
}

// Communication Row Component
function CommunicationRow({
  communication,
  onRetry,
}: {
  communication: Communication;
  onRetry: (id: string) => void;
}) {
  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Clock className="h-4 w-4 text-yellow-500" />,
    sent: <Send className="h-4 w-4 text-blue-500" />,
    delivered: <CheckCircle className="h-4 w-4 text-green-500" />,
    failed: <XCircle className="h-4 w-4 text-red-500" />,
    bounced: <AlertTriangle className="h-4 w-4 text-orange-500" />,
  };

  return (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      <td className="py-3 px-4">
        <span className="font-mono text-sm text-blue-600">{communication.change_number}</span>
      </td>
      <td className="py-3 px-4 text-sm">{communication.stakeholder_group_name}</td>
      <td className="py-3 px-4 text-sm">{communication.channel}</td>
      <td className="py-3 px-4 text-sm max-w-xs truncate">{communication.subject}</td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-1">
          {statusIcons[communication.status]}
          <span className="text-sm">{communication.status}</span>
        </div>
      </td>
      <td className="py-3 px-4 text-sm">
        {communication.sent_at ? new Date(communication.sent_at).toLocaleString() : '-'}
      </td>
      <td className="py-3 px-4">
        {communication.status === 'failed' && (
          <button
            onClick={() => onRetry(communication.id)}
            className="text-sm text-blue-600 hover:underline"
          >
            Retry
          </button>
        )}
      </td>
    </tr>
  );
}

export default function CommunicationsDashboard() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'overview' | 'changes' | 'templates' | 'history'>(
    'overview'
  );

  // Fetch dashboard data
  const { data: dashboard } = useQuery({
    queryKey: ['change-dashboard'],
    queryFn: () => api.get<ChangeDashboardData>(ENDPOINTS.dashboard),
  });

  // Fetch changes
  const { data: changes = [] } = useQuery({
    queryKey: ['change-records'],
    queryFn: () => api.get<ChangeRecord[]>(ENDPOINTS.changes),
  });

  // Fetch templates
  const { data: templates = [] } = useQuery({
    queryKey: ['communication-templates'],
    queryFn: () => api.get<CommunicationTemplate[]>(ENDPOINTS.templates),
  });

  // Fetch communications
  const { data: communications = [] } = useQuery({
    queryKey: ['communications'],
    queryFn: () => api.get<Communication[]>(ENDPOINTS.communications),
  });

  // Retry communication mutation
  const retryMutation = useMutation({
    mutationFn: (id: string) => api.post<Communication>(ENDPOINTS.communicationRetry(id), {}),
    onSuccess: () => {
      toast.success('Communication queued for retry');
      queryClient.invalidateQueries({ queryKey: ['communications'] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-purple-500" />
            Change Communications
          </h1>
          <p className="text-gray-500 mt-1">
            Manage stakeholder communications, templates, and KB articles for change requests
          </p>
        </div>
      </div>

      {/* Stats */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={FileText}
            label="Total Changes"
            value={dashboard.changes.total}
            color="bg-blue-100 text-blue-600"
          />
          <StatCard
            icon={Send}
            label="Communications Sent"
            value={dashboard.communications.total_sent}
            subtext={`${dashboard.communications.success_rate}% success rate`}
            color="bg-green-100 text-green-600"
          />
          <StatCard
            icon={AlertTriangle}
            label="Pending / Failed"
            value={`${dashboard.communications.pending} / ${dashboard.communications.failed}`}
            color="bg-yellow-100 text-yellow-600"
          />
          <StatCard
            icon={BookOpen}
            label="KB Articles"
            value={dashboard.kb_articles.total_linked}
            subtext={`${dashboard.kb_articles.agent_created} agent-created`}
            color="bg-purple-100 text-purple-600"
          />
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          {(['overview', 'changes', 'templates', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Changes */}
          <div>
            <h3 className="font-semibold text-lg mb-4">Recent Changes</h3>
            <div className="space-y-3">
              {dashboard?.recent_changes.slice(0, 5).map((change: ChangeRecord) => (
                <ChangeCard key={change.id} change={change} />
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Changes by State</h3>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              {dashboard && (
                <div className="space-y-2">
                  {Object.entries(dashboard.changes.by_state).map(([state, count]) => (
                    <div key={state} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{state.replace('_', ' ')}</span>
                      <span className="font-medium">{count as number}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Changes Tab */}
      {activeTab === 'changes' && (
        <div className="space-y-4">
          {changes.map((change: ChangeRecord) => (
            <ChangeCard key={change.id} change={change} />
          ))}
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template: CommunicationTemplate) => (
            <TemplateCard
              key={template.id}
              template={template}
              onPreview={(id) => toast.info(`Preview template ${id}`)}
            />
          ))}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Change
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Stakeholder
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Channel
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Subject
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Sent
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {communications.map((comm: Communication) => (
                  <CommunicationRow
                    key={comm.id}
                    communication={comm}
                    onRetry={(id) => retryMutation.mutate(id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
