from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, jsonify)
from app.database import get_db
from app.utils import login_required

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/messages')
@login_required
def messages():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""SELECT DISTINCT
                   CASE WHEN m.sender_id=%s THEN m.receiver_id ELSE m.sender_id END as other_id,
                   u.name as other_name, u.role as other_role,
                   MAX(m.created_at) as last_time
                   FROM messages m
                   JOIN users u ON u.id = CASE WHEN m.sender_id=%s
                                               THEN m.receiver_id ELSE m.sender_id END
                   WHERE m.sender_id=%s OR m.receiver_id=%s
                   GROUP BY other_id ORDER BY last_time DESC""",
                (uid, uid, uid, uid))
    conversations = cur.fetchall()
    cur.close(); db.close()
    return render_template('shared/messages.html', conversations=conversations)


@messages_bp.route('/messages/<int:other_id>', methods=['GET', 'POST'])
@login_required
def conversation(other_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            cur.execute("INSERT INTO messages (sender_id,receiver_id,content) VALUES (%s,%s,%s)",
                        (uid, other_id, content))
            cur.execute("UPDATE messages SET is_read=1 WHERE sender_id=%s AND receiver_id=%s",
                        (other_id, uid))
            db.commit()
        return redirect(url_for('messages.conversation', other_id=other_id))
    cur.execute("""SELECT m.*, u.name as sender_name FROM messages m
                   JOIN users u ON m.sender_id=u.id
                   WHERE (m.sender_id=%s AND m.receiver_id=%s)
                      OR (m.sender_id=%s AND m.receiver_id=%s)
                   ORDER BY m.created_at ASC""", (uid, other_id, other_id, uid))
    msgs = cur.fetchall()
    cur.execute("UPDATE messages SET is_read=1 WHERE sender_id=%s AND receiver_id=%s",
                (other_id, uid))
    db.commit()
    cur.execute("SELECT id, name, role FROM users WHERE id=%s", (other_id,))
    other = cur.fetchone()
    cur.close(); db.close()
    return render_template('shared/conversation.html', msgs=msgs, other=other)


@messages_bp.route('/api/unread-count')
@login_required
def unread_count():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=%s AND is_read=0",
                (session['user_id'],))
    count = cur.fetchone()[0]
    cur.close(); db.close()
    return jsonify({'count': count})
