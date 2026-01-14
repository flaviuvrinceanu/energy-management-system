import React, { useEffect, useMemo, useRef, useState } from 'react';

function AdminSupportInbox() {
	const [ws, setWs] = useState(null);
	const [isConnected, setIsConnected] = useState(false);
	const [threads, setThreads] = useState({});
	const [activeUserId, setActiveUserId] = useState(null);
	const [replyText, setReplyText] = useState('');
	const messagesEndRef = useRef(null);

	const orderedUserIds = useMemo(() => {
		const items = Object.entries(threads).map(([userId, t]) => ({
			userId,
			lastAt: t.lastAt || 0,
			unread: t.unread || 0,
		}));
		items.sort((a, b) => b.lastAt - a.lastAt);
		return items.map((i) => i.userId);
	}, [threads]);

	const activeMessages = useMemo(() => {
		if (!activeUserId || !threads[activeUserId]) return [];
		return threads[activeUserId].messages || [];
	}, [activeUserId, threads]);

	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [activeMessages.length, activeUserId]);

	useEffect(() => {
		const token = localStorage.getItem('token');
		if (!token) return;

		const websocket = new WebSocket(`ws://localhost:8006/ws/chat?token=${token}`);

		websocket.onopen = () => {
			setIsConnected(true);
		};

		websocket.onmessage = (event) => {
			let data;
			try {
				data = JSON.parse(event.data);
			} catch {
				return;
			}
			if (data.type === 'pong') return;

			if (data.type === 'new_user_message') {
				const userId = data.user_id;
				const now = Date.now();
				setThreads((prev) => {
					const existing = prev[userId] || { messages: [], unread: 0, lastAt: 0 };
					const nextMessage = {
						direction: 'in',
						text: data.message || '',
						at: data.timestamp ? new Date(data.timestamp) : new Date(),
					};
					const isActive = userId === activeUserId;
					return {
						...prev,
						[userId]: {
							messages: [...existing.messages, nextMessage],
							unread: isActive ? 0 : (existing.unread || 0) + 1,
							lastAt: now,
						},
					};
				});
				if (!activeUserId) setActiveUserId(userId);
			}
		};

		websocket.onerror = () => {
			setIsConnected(false);
		};

		websocket.onclose = () => {
			setIsConnected(false);
		};

		setWs(websocket);
		return () => {
			websocket.close();
		};
		
	}, []);

	const selectThread = (userId) => {
		setActiveUserId(userId);
		setThreads((prev) => {
			const t = prev[userId];
			if (!t) return prev;
			return { ...prev, [userId]: { ...t, unread: 0 } };
		});
	};

	const sendReply = () => {
		if (!ws || !isConnected) return;
		if (!activeUserId) return;
		const trimmed = replyText.trim();
		if (!trimmed) return;

		ws.send(
			JSON.stringify({
				target_user_id: activeUserId,
				message: trimmed,
				timestamp: new Date().toISOString(),
			})
		);

		setThreads((prev) => {
			const existing = prev[activeUserId] || { messages: [], unread: 0, lastAt: 0 };
			const now = Date.now();
			return {
				...prev,
				[activeUserId]: {
					...existing,
					messages: [
						...existing.messages,
						{ direction: 'out', text: trimmed, at: new Date() },
					],
					lastAt: now,
				},
			};
		});

		setReplyText('');
	};

	const onKeyDown = (e) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendReply();
		}
	};

	return (
		<div style={{ display: 'flex', gap: '16px', height: '70vh' }}>
			<div style={{ width: '320px', border: '1px solid #dee2e6', borderRadius: '8px', overflow: 'hidden' }}>
				<div style={{ padding: '12px', background: '#343a40', color: 'white' }}>
					<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
						<strong>Support Inbox</strong>
						<small style={{ opacity: 0.85 }}>{isConnected ? 'Connected' : 'Disconnected'}</small>
					</div>
				</div>
				<div style={{ maxHeight: 'calc(70vh - 48px)', overflowY: 'auto' }}>
					{orderedUserIds.length === 0 && (
						<div style={{ padding: '12px', color: '#6c757d' }}>No forwarded messages yet.</div>
					)}
					{orderedUserIds.map((userId) => (
						<button
							key={userId}
							onClick={() => selectThread(userId)}
							style={{
								width: '100%',
								textAlign: 'left',
								padding: '10px 12px',
								border: 'none',
								borderBottom: '1px solid #f1f3f5',
								background: userId === activeUserId ? '#e9ecef' : 'white',
								cursor: 'pointer',
							}}
						>
							<div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
								<span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{userId}</span>
								{(threads[userId]?.unread || 0) > 0 && (
									<span style={{ background: '#dc3545', color: 'white', borderRadius: '12px', padding: '2px 8px', fontSize: '12px' }}>
										{threads[userId].unread}
									</span>
								)}
							</div>
						</button>
					))}
				</div>
			</div>

			<div style={{ flex: 1, border: '1px solid #dee2e6', borderRadius: '8px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
				<div style={{ padding: '12px', background: '#007bff', color: 'white' }}>
					<strong>Thread</strong>
					{activeUserId && <span style={{ marginLeft: '10px', fontFamily: 'monospace' }}>{activeUserId}</span>}
				</div>
				<div style={{ flex: 1, overflowY: 'auto', padding: '12px', background: '#f8f9fa' }}>
					{!activeUserId && <div style={{ color: '#6c757d' }}>Select a user to view messages.</div>}
					{activeUserId && activeMessages.map((m, idx) => (
						<div key={idx} style={{ display: 'flex', justifyContent: m.direction === 'out' ? 'flex-end' : 'flex-start', marginBottom: '8px' }}>
							<div
								style={{
									maxWidth: '75%',
									padding: '10px',
									borderRadius: '10px',
									background: m.direction === 'out' ? '#28a745' : '#e9ecef',
									color: m.direction === 'out' ? 'white' : 'black',
								}}
							>
								<div style={{ fontSize: '14px' }}>{m.text}</div>
								<div style={{ fontSize: '10px', opacity: 0.7, marginTop: '4px' }}>
									{m.at instanceof Date ? m.at.toLocaleString() : new Date(m.at).toLocaleString()}
								</div>
							</div>
						</div>
					))}
					<div ref={messagesEndRef} />
				</div>
				<div style={{ padding: '12px', borderTop: '1px solid #dee2e6', background: 'white' }}>
					<div style={{ display: 'flex', gap: '10px' }}>
						<input
							type="text"
							value={replyText}
							onChange={(e) => setReplyText(e.target.value)}
							onKeyDown={onKeyDown}
							placeholder={activeUserId ? 'Type a reply…' : 'Select a thread first…'}
							disabled={!isConnected || !activeUserId}
							style={{ flex: 1, padding: '10px', border: '1px solid #dee2e6', borderRadius: '6px' }}
						/>
						<button
							onClick={sendReply}
							disabled={!isConnected || !activeUserId || !replyText.trim()}
							style={{ padding: '10px 16px', background: '#28a745', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
						>
							Send
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}

export default AdminSupportInbox;
