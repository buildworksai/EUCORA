export function MeshBackground() {
    return (
        <div className="fixed inset-0 -z-10 overflow-hidden bg-background">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-eucora-deepBlue/20 blur-[120px] animate-pulse-slow" />
            <div className="absolute top-[20%] right-[-5%] w-[30%] h-[30%] rounded-full bg-eucora-teal/20 blur-[100px] animate-pulse-slow delay-75" />
            <div className="absolute bottom-[-10%] left-[20%] w-[50%] h-[50%] rounded-full bg-purple-500/10 blur-[120px] animate-pulse-slow delay-150" />
            <div className="absolute bottom-[10%] right-[10%] w-[20%] h-[20%] rounded-full bg-eucora-gold/10 blur-[80px]" />

            {/* Grid Overlay for Tech Feel */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" style={{ opacity: 0.03 }} />
        </div>
    );
}
