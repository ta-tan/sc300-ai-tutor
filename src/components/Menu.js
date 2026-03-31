import React from 'react';

const Menu = ({ stats, onStart }) => {
  // 分野別の進捗（本来はDBから取得）
  const categories = [
    { name: "条件付きアクセス", total: 50, cleared: 20, color: "#007bff" },
    { name: "PIM (特権ID管理)", total: 30, cleared: 15, color: "#28a745" },
    { name: "ユーザーとグループ", total: 40, cleared: 40, color: "#ffc107" }, // 金ランクイメージ
  ];

  return (
    <div style={{ padding: '20px', maxWidth: '500px', margin: 'auto', fontFamily: 'sans-serif' }}>
      <h2 style={{ textAlign: 'center', color: '#333' }}>🎓 SC-300 合格マネージャー</h2>

      {/* 総合進捗パネル (Ping-Tのトップ風) */}
      <div style={{ background: '#343a40', color: '#fff', padding: '20px', borderRadius: '15px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          <div><small>ミス</small><br/><b style={{ fontSize: '1.2rem', color: '#ff6b6b' }}>{stats.miss}</b></div>
          <div><small>ヒット</small><br/><b style={{ fontSize: '1.2rem', color: '#51cf66' }}>{stats.hit}</b></div>
          <div><small>コンボ</small><br/><b style={{ fontSize: '1.2rem', color: '#fcc419' }}>{stats.combo}</b></div>
        </div>
        <div style={{ marginTop: '15px', height: '10px', background: '#495057', borderRadius: '5px', overflow: 'hidden' }}>
          <div style={{ width: '45%', height: '100%', background: 'linear-gradient(90deg, #51cf66, #fcc419)' }}></div>
        </div>
        <p style={{ textAlign: 'right', fontSize: '0.8rem', marginTop: '5px' }}>現在のLv: 12 / 40</p>
      </div>

      {/* カテゴリ選択リスト */}
      <h3>分野別演習</h3>
      {categories.map(cat => (
        <div 
          key={cat.name} 
          onClick={() => onStart(cat.name)}
          style={{ 
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '15px', border: '1px solid #ddd', borderRadius: '10px', marginBottom: '10px',
            cursor: 'pointer', transition: '0.2s', backgroundColor: '#fff'
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#fff'}
        >
          <div>
            <div style={{ fontWeight: 'bold' }}>{cat.name}</div>
            <small style={{ color: '#666' }}>{cat.cleared} / {cat.total} 問完了</small>
          </div>
          <div style={{ 
            width: '40px', height: '40px', borderRadius: '50%', border: `3px solid ${cat.color}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 'bold'
          }}>
            {Math.round((cat.cleared / cat.total) * 100)}%
          </div>
        </div>
      ))}

      <button style={{ 
        width: '100%', padding: '15px', background: '#007bff', color: '#fff', 
        border: 'none', borderRadius: '10px', fontSize: '1rem', fontWeight: 'bold', marginTop: '10px'
      }}>
        模擬試験モード (全範囲)
      </button>
    </div>
  );
};

export default Menu;
