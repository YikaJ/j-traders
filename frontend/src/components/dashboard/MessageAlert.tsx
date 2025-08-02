import React from 'react';

interface MessageAlertProps {
  message: { type: 'success' | 'error' | 'info' | 'warning', text: string } | null;
}

const MessageAlert: React.FC<MessageAlertProps> = ({ message }) => {
  if (!message) return null;

  return (
    <div className={`alert ${
      message.type === 'success' ? 'alert-success' : 
      message.type === 'error' ? 'alert-error' : 
      message.type === 'warning' ? 'alert-warning' : 'alert-info'
    } shadow-lg`}>
      <span>{message.text}</span>
    </div>
  );
};

export default MessageAlert; 