from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from app import app, db
from models import User, Listing, ChatMessage
from datetime import datetime
from sqlalchemy import func

@app.route('/chat')
@login_required
def chat_index():
    # Get all conversations for current user
    conversations = db.session.query(
        ChatMessage.sender_id,
        ChatMessage.receiver_id,
        func.max(ChatMessage.created_at).label('last_message_time')
    ).filter(
        db.or_(
            ChatMessage.sender_id == current_user.id,
            ChatMessage.receiver_id == current_user.id
        )
    ).group_by(
        ChatMessage.sender_id, ChatMessage.receiver_id
    ).all()
    
    # Process conversations to get unique chat partners
    chat_partners = {}
    for conv in conversations:
        partner_id = conv.sender_id if conv.sender_id != current_user.id else conv.receiver_id
        if partner_id not in chat_partners or conv.last_message_time > chat_partners[partner_id]['last_message_time']:
            chat_partners[partner_id] = {
                'user': User.query.get(partner_id),
                'last_message_time': conv.last_message_time
            }
    
    # Get last message for each conversation
    for partner_id, data in chat_partners.items():
        last_message = ChatMessage.query.filter(
            db.or_(
                db.and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == partner_id),
                db.and_(ChatMessage.sender_id == partner_id, ChatMessage.receiver_id == current_user.id)
            )
        ).order_by(ChatMessage.created_at.desc()).first()
        
        data['last_message'] = last_message
        
        # Count unread messages from this partner
        data['unread_count'] = ChatMessage.query.filter_by(
            sender_id=partner_id,
            receiver_id=current_user.id,
            is_read=False
        ).count()
    
    # Sort by last message time
    sorted_partners = sorted(
        chat_partners.values(),
        key=lambda x: x['last_message_time'],
        reverse=True
    )
    
    return render_template('chat/index.html', chat_partners=sorted_partners)

@app.route('/chat/<int:user_id>')
@login_required
def chat_conversation(user_id):
    partner = User.query.get_or_404(user_id)
    
    if partner.id == current_user.id:
        flash('Vous ne pouvez pas chatter avec vous-même.', 'error')
        return redirect(url_for('chat_index'))
    
    # Get all messages between current user and partner
    messages = ChatMessage.query.filter(
        db.or_(
            db.and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
            db.and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id)
        )
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark all messages from partner as read
    ChatMessage.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template('chat/conversation.html', partner=partner, messages=messages)

@app.route('/chat/<int:user_id>/send', methods=['POST'])
@login_required
def send_message(user_id):
    partner = User.query.get_or_404(user_id)
    message_text = request.form.get('message', '').strip()
    listing_id = request.form.get('listing_id', type=int)
    
    if not message_text:
        return jsonify({'error': 'Message vide'}), 400
    
    if partner.id == current_user.id:
        return jsonify({'error': 'Impossible d\'envoyer un message à soi-même'}), 400
    
    # Create new message
    message = ChatMessage(
        sender_id=current_user.id,
        receiver_id=user_id,
        message=message_text,
        listing_id=listing_id
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'message': message.message,
            'created_at': message.created_at.strftime('%H:%M'),
            'sender_name': current_user.full_name
        }
    })

@app.route('/chat/start/<int:listing_id>')
@login_required
def start_chat_from_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    
    if listing.user_id == current_user.id:
        flash('Vous ne pouvez pas chatter sur votre propre annonce.', 'error')
        return redirect(url_for('listing_detail', id=listing_id))
    
    return redirect(url_for('chat_conversation', user_id=listing.user_id))

@app.route('/api/chat/messages/<int:user_id>')
@login_required
def get_messages(user_id):
    """API endpoint to get messages for real-time chat"""
    since = request.args.get('since', type=int)
    
    query = ChatMessage.query.filter(
        db.or_(
            db.and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
            db.and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id)
        )
    ).order_by(ChatMessage.created_at.asc())
    
    if since:
        query = query.filter(ChatMessage.id > since)
    
    messages = query.all()
    
    # Mark new messages from partner as read
    if since:
        ChatMessage.query.filter(
            ChatMessage.sender_id == user_id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.id > since,
            ChatMessage.is_read == False
        ).update({'is_read': True})
        db.session.commit()
    
    return jsonify([{
        'id': msg.id,
        'message': msg.message,
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.full_name,
        'created_at': msg.created_at.strftime('%H:%M'),
        'is_own': msg.sender_id == current_user.id
    } for msg in messages])

@app.route('/api/chat/unread-count')
@login_required
def get_unread_count():
    """API endpoint to get total unread message count"""
    count = ChatMessage.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'unread_count': count})
