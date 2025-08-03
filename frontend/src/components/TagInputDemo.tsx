import React, { useState, useEffect } from 'react';
import TagInput, { Tag } from './common/TagInput';
import { factorApi, FactorTag } from '../services/api';

const TagInputDemo: React.FC = () => {
  const [selectedTags, setSelectedTags] = useState<Tag[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadAvailableTags();
  }, []);

  const loadAvailableTags = async () => {
    try {
      setIsLoading(true);
      const tags = await factorApi.getAllFactorTags(true);
      setAvailableTags(tags);
    } catch (error) {
      console.error('加载标签失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTag = async (tagName: string): Promise<Tag | null> => {
    try {
      const newTag = await factorApi.createFactorTag({
        name: tagName.toLowerCase().replace(/\s+/g, '_'),
        display_name: tagName,
        description: `用户创建的标签: ${tagName}`,
        color: '#3B82F6',
      });
      
      setAvailableTags(prev => [...prev, newTag]);
      return newTag;
    } catch (error) {
      console.error('创建标签失败:', error);
      return null;
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-base-content mb-4">
          TagInput 组件演示
        </h1>
        <p className="text-base-content/70">
          这是一个自定义的TagInput组件，支持选择现有标签和创建新标签。
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 基本用法 */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">基本用法</h2>
            <p className="text-sm text-base-content/70 mb-4">
              选择或创建标签，最多5个标签
            </p>
            
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <span className="loading loading-spinner loading-md"></span>
                <span className="ml-2">加载标签中...</span>
              </div>
            ) : (
              <TagInput
                tags={selectedTags}
                availableTags={availableTags}
                onTagsChange={setSelectedTags}
                onCreateTag={handleCreateTag}
                placeholder="选择或创建标签..."
                maxTags={5}
              />
            )}

            <div className="mt-4">
              <h3 className="font-medium mb-2">已选择的标签:</h3>
              {selectedTags.length === 0 ? (
                <p className="text-base-content/50 text-sm">暂无选择的标签</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {selectedTags.map((tag) => (
                    <span
                      key={tag.id}
                      className="badge badge-primary"
                      style={{ 
                        backgroundColor: tag.color ? `${tag.color}20` : undefined,
                        color: tag.color || undefined
                      }}
                    >
                      {tag.display_name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 功能说明 */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">功能特性</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-primary mb-2">✓ 选择现有标签</h3>
                <p className="text-sm text-base-content/70">
                  从下拉列表中搜索并选择已存在的标签
                </p>
              </div>
              
              <div>
                <h3 className="font-medium text-primary mb-2">✓ 创建新标签</h3>
                <p className="text-sm text-base-content/70">
                  输入新标签名称，自动创建并添加到选择列表
                </p>
              </div>
              
              <div>
                <h3 className="font-medium text-primary mb-2">✓ 标签管理</h3>
                <p className="text-sm text-base-content/70">
                  点击标签上的 X 按钮可以移除已选择的标签
                </p>
              </div>
              
              <div>
                <h3 className="font-medium text-primary mb-2">✓ 键盘操作</h3>
                <p className="text-sm text-base-content/70">
                  支持 Enter 键选择，Backspace 键删除最后一个标签
                </p>
              </div>
              
              <div>
                <h3 className="font-medium text-primary mb-2">✓ 数量限制</h3>
                <p className="text-sm text-base-content/70">
                  可以设置最大标签数量，超出后无法继续添加
                </p>
              </div>
              
              <div>
                <h3 className="font-medium text-primary mb-2">✓ 颜色支持</h3>
                <p className="text-sm text-base-content/70">
                  每个标签可以设置自定义颜色，支持主题色
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 可用标签列表 */}
      <div className="mt-8 card bg-base-100 shadow-xl">
        <div className="card-body">
          <h2 className="card-title">可用标签列表</h2>
          <p className="text-sm text-base-content/70 mb-4">
            当前系统中所有可用的标签
          </p>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <span className="loading loading-spinner loading-sm"></span>
              <span className="ml-2">加载中...</span>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {availableTags.map((tag) => (
                <div
                  key={tag.id}
                  className="p-3 rounded-lg border border-base-300 bg-base-50"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tag.color || '#3B82F6' }}
                    />
                    <span className="font-medium text-sm">{tag.display_name}</span>
                  </div>
                  <div className="text-xs text-base-content/50">
                    {tag.name}
                  </div>
                  {tag.description && (
                    <div className="text-xs text-base-content/60 mt-1">
                      {tag.description}
                    </div>
                  )}
                  <div className="text-xs text-base-content/40 mt-2">
                    使用次数: {tag.usage_count}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TagInputDemo; 