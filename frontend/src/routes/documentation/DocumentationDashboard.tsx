// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E12: Documentation Agent Dashboard
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { FileText, GitBranch, Play, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type CodeRepository, type CodeAnalysis, type GeneratedDocument } from './contracts';

export default function DocumentationDashboard() {
  const queryClient = useQueryClient();
  const [selectedRepo] = useState<string | null>(null);

  const { data: repositories } = useQuery({
    queryKey: ['documentation', 'repositories'],
    queryFn: () => api.get<CodeRepository[]>(ENDPOINTS.repositories),
  });

  const { data: analyses } = useQuery({
    queryKey: ['documentation', 'analyses', selectedRepo],
    queryFn: async () => {
      const url = selectedRepo ? `${ENDPOINTS.analyses}?repository_id=${selectedRepo}` : ENDPOINTS.analyses;
      return api.get<CodeAnalysis[]>(url);
    },
    enabled: !!selectedRepo,
  });

  const { data: documents } = useQuery({
    queryKey: ['documentation', 'documents'],
    queryFn: () => api.get<GeneratedDocument[]>(ENDPOINTS.documents),
  });

  const analyzeMutation = useMutation({
    mutationFn: async (repoId: string) => {
      return api.post(ENDPOINTS.repositoryAnalyze(repoId), {});
    },
    onSuccess: () => {
      toast.success('Analysis started');
      queryClient.invalidateQueries({ queryKey: ['documentation'] });
    },
    onError: () => {
      toast.error('Failed to start analysis');
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Documentation Agent</h1>
      </div>

      {/* Repositories */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Repositories</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {repositories?.map((repo: CodeRepository) => (
            <div
              key={repo.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <GitBranch className="h-5 w-5 text-blue-500" />
                  <h3 className="font-medium">{repo.name}</h3>
                </div>
                <button
                  onClick={() => analyzeMutation.mutate(repo.id)}
                  disabled={analyzeMutation.isPending}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {analyzeMutation.isPending ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </button>
              </div>
              <p className="text-sm text-gray-500">{repo.repo_type}</p>
              {repo.last_analyzed && (
                <p className="text-xs text-gray-400 mt-2">
                  Last analyzed: {new Date(repo.last_analyzed).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Recent Analyses */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Recent Analyses</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Repository</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Branch</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Modules</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Started</th>
              </tr>
            </thead>
            <tbody>
              {analyses?.slice(0, 10).map((analysis: CodeAnalysis) => (
                <tr key={analysis.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm">{analysis.repository_name}</td>
                  <td className="px-4 py-3 text-sm">{analysis.branch}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        analysis.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : analysis.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {analysis.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{analysis.module_count}</td>
                  <td className="px-4 py-3 text-sm">
                    {analysis.started_at ? new Date(analysis.started_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Generated Documents */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Generated Documents</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents?.slice(0, 9).map((doc: GeneratedDocument) => (
            <div
              key={doc.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-5 w-5 text-blue-500" />
                <h3 className="font-medium">{doc.title}</h3>
              </div>
              <p className="text-sm text-gray-500 mb-2">{doc.doc_type}</p>
              <div className="flex items-center justify-between">
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    doc.status === 'published'
                      ? 'bg-green-100 text-green-800'
                      : doc.status === 'review'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {doc.status}
                </span>
                {doc.published_at && (
                  <span className="text-xs text-gray-400">
                    {new Date(doc.published_at).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
