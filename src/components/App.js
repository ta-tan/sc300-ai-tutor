import React, { useState, useEffect } from 'react';

// ダミーデータ（本来はAzure Functions経由でDBから取得）
const sampleQuestions = [
  {
    id: 1,
    category: "条件付きアクセス",
    question: "「すべての信頼できる場所」を許可し、「日本」をブロックするポリシーがある場合、日本の信頼できるIPからのアクセスはどうなりますか？",
    options: ["許可される", "ブロックされる", "MFAを要求される", "セッションが制限される"],
    answer: "ブロックされる",
    explanation: "条件付きアクセスでは「ブロック」が「許可」よりも常に優先されます。"
  },
  {
    id: 2,
    category: "PIM",
    question: "PIMにおいて、承認が必要な割り当ての種類はどれですか？",
    options: ["アクティブな割り当て", "対象となる割り当て", "永続的な割り当て", "直接割り当て"],
    answer: "対象となる割り当て",
    explanation: "「対象となる（Eligible）」割り当ては、利用時にアクティブ化の申請と承認（設定による）が必要です。"
  }
];

function App() {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selected, setSelected] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [stats, setStats] = useState({ miss: 0, hit: 0, combo: 0 });

  const currentQ = sampleQuestions[currentIdx];

  const handleAnswer = (opt) => {
    if (showExplanation) return;
    setSelected(opt);
    setShowExplanation(true);

    if (opt === currentQ.answer) {
      setStats(prev => ({ ...prev, hit: prev.hit + 1, combo: prev.combo + 1 }));
    } else {
      setStats(prev => ({ ...prev, miss: prev.miss + 1, combo: 0 }));
    }
  };

  const nextQuestion = () => {
    setSelected(null);
    setShowExplanation(false);
    setCurrentIdx((currentIdx + 1) % sampleQuestions.length);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: 'auto', fontFamily: 'sans-serif' }}>
      {/* ステータスバー (Ping-T風) */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', padding: '10px', background: '#f0f0f0', borderRadius: '8px' }}>
        <span>❌ ミス: {stats.miss}</span>
        <span>✅ ヒット: {stats.hit}</span>
        <span style={{ color: stats.combo >= 2 ? 'gold' : 'black', fontWeight: 'bold' }}>
          🔥 コンボ: {stats.combo} {stats.combo >= 2 && 'GOLD!!'}
        </span>
      </div>

      {/* 問題表示エリア */}
      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '10px', minHeight: '200px' }}>
        <small style={{ color: '#666' }}>[{currentQ.category}]</small>
        <h3>Q{currentIdx + 1}. {currentQ.question}</h3>
        
        <div style={{ display: 'grid', gap: '10px' }}>
          {currentQ.options.map(opt => (
            <button
              key={opt}
              onClick={() => handleAnswer(opt)}
              style={{
                padding: '12px',
                textAlign: 'left',
                backgroundColor: showExplanation 
                  ? (opt === currentQ.answer ? '#d4edda' : (opt === selected ? '#f8d7da' : '#fff'))
                  : '#fff',
                border: '1px solid #ddd',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* 解説エリア */}
      {showExplanation && (
        <div style={{ marginTop: '20px', padding: '15px', background: '#e9ecef', borderRadius: '10px' }}>
          <strong style={{ color: selected === currentQ.answer ? 'green' : 'red' }}>
            {selected === currentQ.answer ? '正解！' : '不正解...'}
          </strong>
          <p>{currentQ.explanation}</p>
          <button onClick={nextQuestion} style={{ width: '100%', padding: '10px', background: '#007bff', color: '#fff', border: 'none', borderRadius: '5px' }}>
            次の問題へ
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
