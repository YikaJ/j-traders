import React, { useState, useRef, useEffect } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { Listbox } from '@headlessui/react';

export interface Tag {
  id: string;
  name: string;
  display_name: string;
  color?: string;
}

interface TagInputProps {
  tags: Tag[];
  availableTags: Tag[];
  onTagsChange: (tags: Tag[]) => void;
  onCreateTag?: (tagName: string) => Promise<Tag | null>;
  placeholder?: string;
  disabled?: boolean;
  maxTags?: number;
  className?: string;
}

const TagInput: React.FC<TagInputProps> = ({
  tags,
  availableTags,
  onTagsChange,
  onCreateTag,
  placeholder = "选择或创建标签...",
  disabled = false,
  maxTags = 10,
  className = ""
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 过滤可用的标签（排除已选择的）
  const availableOptions = availableTags.filter(
    tag => !tags.some(selectedTag => selectedTag.id === tag.id)
  );

  // 处理输入变化
  const handleInputChange = (value: string) => {
    setInputValue(value);
    if (value.trim()) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  };

  // 添加标签
  const addTag = (tag: Tag) => {
    if (tags.length >= maxTags) return;
    
    if (!tags.some(t => t.id === tag.id)) {
      onTagsChange([...tags, tag]);
    }
    setInputValue('');
    setIsOpen(false);
  };

  // 移除标签
  const removeTag = (tagId: string) => {
    onTagsChange(tags.filter(tag => tag.id !== tagId));
  };

  // 创建新标签
  const handleCreateTag = async () => {
    const tagName = inputValue.trim();
    if (!tagName || !onCreateTag) return;

    setIsCreating(true);
    try {
      const newTag = await onCreateTag(tagName);
      if (newTag) {
        addTag(newTag);
      }
    } catch (error) {
      console.error('创建标签失败:', error);
    } finally {
      setIsCreating(false);
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      if (availableOptions.length > 0) {
        addTag(availableOptions[0]);
      } else if (onCreateTag) {
        handleCreateTag();
      }
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      removeTag(tags[tags.length - 1].id);
    }
  };

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`}>
      {/* 标签容器 */}
      <div className="min-h-[2.5rem] p-2 border border-base-300 rounded-lg bg-base-100 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
        <div className="flex flex-wrap gap-2">
          {/* 已选择的标签 */}
          {tags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 px-2 py-1 text-sm rounded-md bg-primary/10 text-primary border border-primary/20"
              style={{ 
                backgroundColor: tag.color ? `${tag.color}20` : undefined,
                borderColor: tag.color ? `${tag.color}40` : undefined,
                color: tag.color || undefined
              }}
            >
              <span className="truncate max-w-[120px]">{tag.display_name}</span>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeTag(tag.id)}
                  className="ml-1 hover:bg-primary/20 rounded-full p-0.5 transition-colors"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              )}
            </span>
          ))}

          {/* 输入框 */}
          {tags.length < maxTags && (
            <div className="relative flex-1 min-w-[120px]">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsOpen(true)}
                placeholder={tags.length === 0 ? placeholder : ""}
                disabled={disabled}
                className="w-full bg-transparent outline-none text-sm placeholder-base-content/50"
              />
            </div>
          )}
        </div>
      </div>

      {/* 下拉选项 */}
      {isOpen && (availableOptions.length > 0 || onCreateTag) && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-lg shadow-lg max-h-60 overflow-auto"
        >
          <div className="py-1">
            {/* 可用标签选项 */}
            {availableOptions
              .filter(tag => 
                tag.display_name.toLowerCase().includes(inputValue.toLowerCase()) ||
                tag.name.toLowerCase().includes(inputValue.toLowerCase())
              )
              .map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => addTag(tag)}
                  className="w-full px-3 py-2 text-left hover:bg-base-200 transition-colors flex items-center gap-2"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: tag.color || '#3B82F6' }}
                  />
                  <span className="truncate">{tag.display_name}</span>
                  <span className="text-xs text-base-content/50 ml-auto">
                    {tag.name}
                  </span>
                </button>
              ))}

            {/* 创建新标签选项 */}
            {onCreateTag && inputValue.trim() && 
             !availableOptions.some(tag => 
               tag.display_name.toLowerCase() === inputValue.toLowerCase() ||
               tag.name.toLowerCase() === inputValue.toLowerCase()
             ) && (
              <button
                type="button"
                onClick={handleCreateTag}
                disabled={isCreating}
                className="w-full px-3 py-2 text-left hover:bg-base-200 transition-colors flex items-center gap-2 text-primary"
              >
                <PlusIcon className="w-4 h-4" />
                <span>
                  {isCreating ? '创建中...' : `创建标签 "${inputValue}"`}
                </span>
              </button>
            )}

            {/* 无选项提示 */}
            {availableOptions.length === 0 && !onCreateTag && (
              <div className="px-3 py-2 text-sm text-base-content/50">
                暂无可用标签
              </div>
            )}
          </div>
        </div>
      )}

      {/* 标签数量提示 */}
      {tags.length >= maxTags && (
        <div className="mt-1 text-xs text-base-content/50">
          最多可选择 {maxTags} 个标签
        </div>
      )}
    </div>
  );
};

export default TagInput; 