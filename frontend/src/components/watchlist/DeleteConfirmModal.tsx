import React from 'react';
import { WatchlistStock } from '../../services/api';

interface DeleteConfirmModalProps {
  visible: boolean;
  stock: WatchlistStock | null;
  onClose: () => void;
  onConfirm: () => void;
}

const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  visible,
  stock,
  onClose,
  onConfirm
}) => {
  if (!visible || !stock) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box">
        <h3 className="font-bold text-lg">确认删除</h3>
        <p className="py-4">
          确定要从自选股中移除 <strong>{stock.name}</strong> 吗？
        </p>
        <div className="modal-action">
          <button 
            className="btn"
            onClick={onClose}
          >
            取消
          </button>
          <button 
            className="btn btn-error"
            onClick={onConfirm}
          >
            确定移除
          </button>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
};

export default DeleteConfirmModal; 