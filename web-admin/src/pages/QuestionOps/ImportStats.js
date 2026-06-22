import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, message } from 'antd';
import { getImportStats } from '../../services/api';
import './ImportStats.css';

const ImportStatsPage = () => {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await getImportStats();
      setStats(res.data || {});
    } catch (e) {
      message.error(e.response?.data?.error || '加载统计失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadStats(); }, []);

  const metricCards = [
    { title: '批次数', key: 'batches' },
    { title: '解析题数', key: 'parsed_questions' },
    { title: '通过题数', key: 'approved_questions' },
    { title: '通过率', key: 'approval_rate', suffix: '%' },
    { title: '平均置信度', key: 'average_confidence', suffix: '%' },
    { title: '低置信数', key: 'low_confidence_count' },
    { title: '失败批次', key: 'failed_batches' },
    { title: '批均题数', key: 'average_questions_per_batch' }
  ];

  const listToRows = (value) => Array.isArray(value) ? value : Object.entries(value || {}).map(([name, count]) => ({ name, count }));

  const simpleColumns = [
    { title: '分类', dataIndex: 'name', key: 'name' },
    { title: '数量', dataIndex: 'count', key: 'count' }
  ];

  const formatValue = (card) => {
    const value = stats[card.key] || 0;
    if (card.suffix === '%') return Math.round(Number(value) * 100);
    return value;
  };

  return (
    <div className="stats-page">
      <Row gutter={[16, 16]} className="stats-row">
        {metricCards.map(card => (
          <Col xs={24} sm={12} md={6} key={card.key}>
            <Card loading={loading}>
              <Statistic title={card.title} value={formatValue(card)} suffix={card.suffix} />
            </Card>
          </Col>
        ))}
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card title="按状态" loading={loading}>
            <Table rowKey="name" columns={simpleColumns} dataSource={listToRows(stats.by_status)} pagination={false} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="按科目" loading={loading}>
            <Table rowKey="name" columns={simpleColumns} dataSource={listToRows(stats.by_subject)} pagination={false} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="按来源类型" loading={loading}>
            <Table rowKey="name" columns={simpleColumns} dataSource={listToRows(stats.by_source_type)} pagination={false} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ImportStatsPage;
