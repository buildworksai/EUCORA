import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SkeletonTable } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { AssetDetailDialog } from '@/components/assets/AssetDetailDialog';
import {
    flexRender,
    getCoreRowModel,
    useReactTable,
    getPaginationRowModel,
    getFilteredRowModel,
    ColumnDef,
} from '@tanstack/react-table';
import { Search, Filter, Download, Laptop, Server, Smartphone, Monitor } from 'lucide-react';
import { useAssets, type Asset } from '@/lib/api/hooks/useAssets';

export default function AssetInventory() {
    const [globalFilter, setGlobalFilter] = useState('');
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [page, setPage] = useState(1);
    const pageSize = 50;

    const { data, isLoading, error } = useAssets({
        page,
        page_size: pageSize,
        search: globalFilter || undefined,
    });

    const assets = data?.assets || [];
    const total = data?.total || 0;

    const columns = useMemo<ColumnDef<Asset>[]>(
        () => [
            {
                accessorKey: 'name',
                header: 'Asset Name',
                cell: ({ row }) => (
                    <div className="font-medium text-foreground">{row.getValue('name')}</div>
                ),
            },
            {
                accessorKey: 'type',
                header: 'Type',
                cell: ({ row }) => {
                    const type = row.getValue('type') as string;
                    const Icon =
                        type === 'Laptop'
                            ? Laptop
                            : type === 'Desktop'
                            ? Monitor
                            : type === 'Mobile'
                            ? Smartphone
                            : Server;
                    return (
                        <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4 text-muted-foreground" />
                            <span>{type}</span>
                        </div>
                    );
                },
            },
            {
                accessorKey: 'os',
                header: 'Operating System',
                cell: ({ row }) => (
                    <span className="text-muted-foreground">{row.getValue('os')}</span>
                ),
            },
            {
                accessorKey: 'status',
                header: 'Status',
                cell: ({ row }) => {
                    const status = row.getValue('status') as string;
                    return (
                        <Badge
                            variant={status === 'Active' ? 'default' : 'secondary'}
                            className={status === 'Active' ? 'bg-eucora-green hover:bg-eucora-green-dark' : ''}
                        >
                            {status}
                        </Badge>
                    );
                },
            },
            {
                accessorKey: 'compliance_score',
                header: 'Compliance',
                cell: ({ row }) => {
                    const score = row.getValue('compliance_score') as number;
                    return (
                        <div className="flex items-center gap-2">
                            <div className="w-full h-2 bg-muted rounded-full overflow-hidden w-24">
                                <div
                                    className={`h-full ${
                                        score > 90 ? 'bg-eucora-green' : score > 70 ? 'bg-eucora-gold' : 'bg-eucora-red'
                                    }`}
                                    style={{ width: `${score}%` }}
                                />
                            </div>
                            <span className="text-xs font-mono">{score}%</span>
                        </div>
                    );
                },
            },
            {
                accessorKey: 'location',
                header: 'Location',
            },
            {
                accessorKey: 'owner',
                header: 'Owner',
                cell: ({ row }) => (
                    <span className="text-muted-foreground text-sm">{row.getValue('owner')}</span>
                ),
            },
        ],
        []
    );

    const table = useReactTable({
        data: assets,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        state: { globalFilter },
        onGlobalFilterChange: setGlobalFilter,
        manualPagination: true,
        pageCount: Math.ceil(total / pageSize),
    });

    if (error) {
        return (
            <div className="space-y-6">
                <EmptyState
                    icon={Search}
                    title="Failed to load assets"
                    description={error instanceof Error ? error.message : 'Unknown error occurred'}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <AssetDetailDialog
                asset={selectedAsset}
                open={!!selectedAsset}
                onOpenChange={(open) => !open && setSelectedAsset(null)}
            />

            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Global Asset Inventory (CMDB)</h2>
                    <p className="text-muted-foreground">
                        Real-time visibility into {total.toLocaleString()} endpoint assets.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" aria-label="Export CSV">
                        <Download className="mr-2 h-4 w-4" /> Export CSV
                    </Button>
                    <Button className="bg-eucora-deepBlue text-white" aria-label="Advanced filter">
                        <Filter className="mr-2 h-4 w-4" /> Advanced Filter
                    </Button>
                </div>
            </div>

            <Card className="glass">
                <CardHeader className="pb-3">
                    <div className="flex items-center gap-2">
                        <Search className="w-4 h-4 text-muted-foreground" />
                        <Input
                            placeholder="Search assets (Name, OS, Owner)..."
                            value={globalFilter ?? ''}
                            onChange={(e) => setGlobalFilter(e.target.value)}
                            className="max-w-sm border-none shadow-none focus-visible:ring-0 bg-transparent pl-0 text-base"
                            aria-label="Search assets"
                        />
                    </div>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <SkeletonTable rows={10} />
                    ) : assets.length === 0 ? (
                        <div className="py-12">
                            <EmptyState
                                icon={Search}
                                title="No assets found"
                                description="No assets match your search criteria"
                            />
                        </div>
                    ) : (
                        <>
                            <div className="rounded-xl border bg-card overflow-hidden">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm text-left" role="table">
                                        <thead className="bg-muted/50 text-muted-foreground">
                                            {table.getHeaderGroups().map((headerGroup) => (
                                                <tr key={headerGroup.id} className="border-b">
                                                    {headerGroup.headers.map((header) => (
                                                        <th key={header.id} className="h-12 px-4 align-middle font-medium">
                                                            {header.isPlaceholder
                                                                ? null
                                                                : flexRender(header.column.columnDef.header, header.getContext())}
                                                        </th>
                                                    ))}
                                                </tr>
                                            ))}
                                        </thead>
                                        <tbody>
                                            {table.getRowModel().rows?.length ? (
                                                table.getRowModel().rows.map((row) => (
                                                    <tr
                                                        key={row.id}
                                                        className="border-b transition-colors hover:bg-muted/50 cursor-pointer"
                                                        onClick={() => setSelectedAsset(row.original)}
                                                        role="button"
                                                        tabIndex={0}
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter' || e.key === ' ') {
                                                                setSelectedAsset(row.original);
                                                            }
                                                        }}
                                                    >
                                                        {row.getVisibleCells().map((cell) => (
                                                            <td key={cell.id} className="p-4 align-middle">
                                                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))
                                            ) : (
                                                <tr>
                                                    <td colSpan={columns.length} className="h-24 text-center">
                                                        No results.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="flex items-center justify-end space-x-2 py-4">
                                <div className="text-sm text-muted-foreground">
                                    Page {page} of {Math.ceil(total / pageSize)} ({total} total)
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    aria-label="Previous page"
                                >
                                    Previous
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
                                    disabled={page >= Math.ceil(total / pageSize)}
                                    aria-label="Next page"
                                >
                                    Next
                                </Button>
                            </div>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
