import React, { useState, useEffect } from 'react';
import yaml from 'yaml';
import { useSquadStore } from '@/store/useSquadStore';

interface TwitterPanelProps {
    squadCode: string;
}

export const TwitterPanel: React.FC<TwitterPanelProps> = ({ squadCode }) => {
    const [activeTab, setActiveTab] = useState<'config' | 'results' | 'history'>('config');
    const [config, setConfig] = useState<string>('');
    const [results, setResults] = useState<any>(null);
    const [history, setHistory] = useState<any>(null);
    const [isSaving, setIsSaving] = useState(false);
    
    // Subscribe to global squad state
    const squadState = useSquadStore((s) => s.activeStates.get(squadCode));
    const isRunning = squadState?.status === 'running' || squadState?.status === 'executing';
    const hasError = squadState?.status === 'error';
    const errorMessage = (squadState as any)?.errorMessage;
    const currentStep = squadState?.step?.current || 0;
    const totalSteps = squadState?.step?.total || 5;
    const stepLabel = squadState?.step?.label || '';

    useEffect(() => {
        fetchConfig();
        fetchResults();
        fetchHistory();
    }, []);

    const fetchConfig = async () => {
        try {
            const res = await fetch('/api/squad/twitter/config');
            const data = await res.json();
            setConfig(data.content);
        } catch (e) {
            console.error('Failed to fetch config', e);
        }
    };

    const fetchResults = async () => {
        try {
            const res = await fetch('/api/squad/twitter/results');
            const data = await res.json();
            if (data.content) {
                setResults(yaml.parse(data.content));
            }
        } catch (e) {
            console.error('Failed to fetch results', e);
        }
    };

    const fetchHistory = async () => {
        console.log(`Fetching history for ${squadCode}...`);
        try {
            const res = await fetch('/api/squad/twitter/history');
            const data = await res.json();
            if (data.content) {
                setHistory(yaml.parse(data.content));
            }
        } catch (e) {
            console.error('Failed to fetch history', e);
        }
    };

    const handleSaveConfig = async () => {
        setIsSaving(true);
        try {
            await fetch('/api/squad/twitter/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: config })
            });
            setTimeout(() => setIsSaving(false), 2000);
        } catch (e) {
            setIsSaving(false);
        }
    };

    const handleRun = async () => {
        try {
            const res = await fetch('/api/squad/twitter/run', { method: 'POST' });
            const data = await res.json();
            console.log('Squad started:', data.message);
            // Atualizar resultados após alguns segundos
            setTimeout(() => fetchResults(), 5000);
        } catch (e) {
            console.error('Failed to start squad', e);
        }
    };

    const progressPercentage = (currentStep / totalSteps) * 100;

    return (
        <div style={{
            padding: '20px',
            background: '#1a1b1e',
            color: '#eee',
            borderRadius: '12px',
            border: '1px solid #333',
            height: 'calc(100vh - 100px)',
            display: 'flex',
            flexDirection: 'column',
            fontFamily: 'Inter, system-ui, sans-serif'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ margin: 0, fontSize: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    🐦 Twitter Engagement Panel
                </h1>
                <button
                    onClick={handleRun}
                    disabled={isRunning}
                    style={{
                        padding: '10px 20px',
                        background: isRunning ? '#444' : '#1DA1F2',
                        color: 'white',
                        border: 'none',
                        borderRadius: '20px',
                        fontWeight: 'bold',
                        cursor: isRunning ? 'not-allowed' : 'pointer',
                        transition: '0.2s',
                        boxShadow: isRunning ? 'none' : '0 4px 12px rgba(29, 161, 242, 0.3)'
                    }}
                >
                    {isRunning ? '⏳ Processando...' : '🚀 Rodar Squad'}
                </button>
            </div>

            {/* Error Banner */}
            {hasError && (
                <div style={{ 
                    padding: '12px 15px', 
                    background: 'rgba(255, 68, 68, 0.1)', 
                    border: '1px solid #ff4444',
                    color: '#ff4444',
                    borderRadius: '8px', 
                    marginBottom: '15px', 
                    fontSize: '13px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '5px'
                }}>
                    <strong style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>⚠️ Erro na Execução</strong>
                    <span>{errorMessage || 'Ocorreu um erro inesperado no processamento.'}</span>
                </div>
            )}

            {/* Progress Section */}
            {isRunning && (
                <div style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px', color: '#888' }}>
                        <span>{stepLabel || 'Processando...'}</span>
                        <span>Etapa {currentStep} de {totalSteps}</span>
                    </div>
                    <div style={{ height: '6px', background: '#333', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ 
                            height: '100%', 
                            width: `${progressPercentage}%`, 
                            background: '#1DA1F2', 
                            transition: 'width 0.5s ease' 
                        }} />
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', gap: '20px', borderBottom: '1px solid #333', marginBottom: '20px' }}>
                <div 
                    onClick={() => setActiveTab('config')}
                    style={{ padding: '10px', cursor: 'pointer', borderBottom: activeTab === 'config' ? '2px solid #1DA1F2' : 'none', color: activeTab === 'config' ? '#1DA1F2' : '#888' }}
                >
                    Configuração
                </div>
                <div 
                    onClick={() => setActiveTab('results')}
                    style={{ padding: '10px', cursor: 'pointer', borderBottom: activeTab === 'results' ? '2px solid #1DA1F2' : 'none', color: activeTab === 'results' ? '#1DA1F2' : '#888' }}
                >
                    Tweets Encontrados {results?.posts?.length > 0 && `(${results.posts.length})`}
                </div>
                <div 
                    onClick={() => setActiveTab('history')}
                    style={{ padding: '10px', cursor: 'pointer', borderBottom: activeTab === 'history' ? '2px solid #1DA1F2' : 'none', color: activeTab === 'history' ? '#1DA1F2' : '#888' }}
                >
                    Última Campanha
                </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto' }}>
                {activeTab === 'config' ? (
                    <div>
                        <p style={{ fontSize: '13px', color: '#888', marginBottom: '10px' }}>Edite o foco da pesquisa (Markdown):</p>
                        <textarea 
                            value={config}
                            onChange={(e) => setConfig(e.target.value)}
                            style={{
                                width: '100%',
                                height: '250px',
                                background: '#222',
                                color: '#eee',
                                fontFamily: 'monospace',
                                border: '1px solid #444',
                                borderRadius: '8px',
                                padding: '12px',
                                marginBottom: '10px',
                                outline: 'none',
                                focus: 'border-color: #1DA1F2'
                            }}
                        />
                        <button 
                            onClick={handleSaveConfig}
                            disabled={isSaving}
                            style={{
                                padding: '8px 16px',
                                background: isSaving ? '#22c55e' : '#333',
                                color: 'white',
                                border: '1px solid #555',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '13px',
                                transition: '0.3s'
                            }}
                        >
                            {isSaving ? '✅ Salvo!' : '💾 Salvar Config'}
                        </button>
                    </div>
                ) : activeTab === 'results' ? (
                    <div>
                        {!results?.posts || results.posts.length === 0 ? (
                            <p style={{ color: '#888' }}>Nenhum tweet encontrado ainda. Clique em "Rodar Squad" para buscar.</p>
                        ) : (
                            <div>
                                <p style={{ fontSize: '13px', color: '#888', marginBottom: '15px' }}>
                                    {results.posts.length} tweets encontrados
                                </p>
                                {results.posts.map((post: any) => (
                                    <div key={post.id} style={{ 
                                        background: '#25262b', 
                                        padding: '15px', 
                                        borderRadius: '10px', 
                                        marginBottom: '15px',
                                        borderLeft: '4px solid #1DA1F2'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                                            <div style={{ fontSize: '13px', color: '#1DA1F2', fontWeight: 'bold' }}>
                                                {post.author}
                                            </div>
                                            <div style={{ fontSize: '11px', color: '#666' }}>
                                                ❤️ {post.likes} | 🔄 {post.reposts}
                                            </div>
                                        </div>
                                        <div style={{ whiteSpace: 'pre-wrap', marginBottom: '10px', lineHeight: '1.5', fontSize: '14px' }}>
                                            {post.text}
                                        </div>
                                        <a 
                                            href={post.url} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            style={{ 
                                                fontSize: '12px', 
                                                color: '#1DA1F2', 
                                                textDecoration: 'none',
                                                display: 'inline-block',
                                                marginTop: '5px'
                                            }}
                                        >
                                            🔗 Ver no Twitter/X →
                                        </a>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div>
                        {!history && <p style={{ color: '#888' }}>Nenhuma campanha gerada recentemente.</p>}
                        {history?.checks?.map((check: any) => (
                            <div key={check.id} style={{ 
                                background: '#25262b', 
                                padding: '15px', 
                                borderRadius: '10px', 
                                marginBottom: '15px',
                                borderLeft: '4px solid #1DA1F2'
                            }}>
                                <div style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>ID: {check.id}</div>
                                <div style={{ whiteSpace: 'pre-wrap', marginBottom: '10px', lineHeight: '1.5', fontSize: '14px' }}>
                                    {check.final_output}
                                </div>
                                <div style={{ fontSize: '11px', color: '#666', fontStyle: 'italic', borderTop: '1px solid #333', paddingTop: '8px' }}>
                                    Rita Revisão: {check.notes}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
