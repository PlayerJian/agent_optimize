import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import asyncio
import os
import re

from models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, Document, Chunk
from services.vector_service import VectorService
from services.fulltext_service import FulltextService
from config import settings

logger = logging.getLogger("retrieval")

class KnowledgeBaseService:
    def __init__(self):
        # 在实际应用中，应该连接到PostgreSQL数据库
        # 这里为了演示，使用内存存储
        self.knowledge_bases = []
        self.documents = []
        self.chunks = []
        self.vector_service = VectorService()
        self.fulltext_service = FulltextService()
    
    async def get_all_knowledge_bases(self) -> List[KnowledgeBase]:
        """获取所有知识库"""
        try:
            # 在实际应用中，应该从PostgreSQL数据库查询
            # 如果没有知识库，创建一些模拟数据
            if not self.knowledge_bases:
                await self._create_mock_data()
                
            return self.knowledge_bases
            
        except Exception as e:
            logger.error(f"Get all knowledge bases error: {str(e)}", exc_info=True)
            raise
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取特定知识库"""
        try:
            # 在实际应用中，应该从PostgreSQL数据库查询
            # 如果没有知识库，创建一些模拟数据
            if not self.knowledge_bases:
                await self._create_mock_data()
                
            for kb in self.knowledge_bases:
                if kb.id == kb_id:
                    return kb
                    
            return None
            
        except Exception as e:
            logger.error(f"Get knowledge base error: {str(e)}", exc_info=True)
            raise
    
    async def create_knowledge_base(self, kb_create: KnowledgeBaseCreate) -> KnowledgeBase:
        """创建新知识库"""
        try:
            # 创建知识库对象
            kb = KnowledgeBase(
                id=str(uuid.uuid4()),
                name=kb_create.name,
                description=kb_create.description,
                document_count=0,
                last_updated=datetime.now(),
                status="active",
                created_at=datetime.now()
            )
            
            # 保存知识库
            # 在实际应用中，应该保存到PostgreSQL数据库
            self.knowledge_bases.append(kb)
            
            logger.info(f"Created knowledge base: {kb.name} (ID: {kb.id})")
            return kb
            
        except Exception as e:
            logger.error(f"Create knowledge base error: {str(e)}", exc_info=True)
            raise
    
    async def update_knowledge_base(self, kb_id: str, kb_update: KnowledgeBaseUpdate) -> Optional[KnowledgeBase]:
        """更新知识库"""
        try:
            # 查找知识库
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                return None
                
            # 更新字段
            if kb_update.name is not None:
                kb.name = kb_update.name
                
            if kb_update.description is not None:
                kb.description = kb_update.description
                
            if kb_update.status is not None:
                kb.status = kb_update.status
                
            kb.last_updated = datetime.now()
            
            logger.info(f"Updated knowledge base: {kb.name} (ID: {kb.id})")
            return kb
            
        except Exception as e:
            logger.error(f"Update knowledge base error: {str(e)}", exc_info=True)
            raise
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        try:
            # 查找知识库
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                return False
                
            # 删除知识库中的所有文档
            docs = await self.get_documents(kb_id)
            for doc in docs:
                await self.delete_document(kb_id, doc.id)
                
            # 删除知识库
            # 在实际应用中，应该从PostgreSQL数据库删除
            self.knowledge_bases = [kb for kb in self.knowledge_bases if kb.id != kb_id]
            
            # 删除向量数据库中的向量
            await self.vector_service.delete_by_knowledge_base(kb_id)
            
            logger.info(f"Deleted knowledge base: {kb.name} (ID: {kb.id})")
            return True
            
        except Exception as e:
            logger.error(f"Delete knowledge base error: {str(e)}", exc_info=True)
            raise
    
    async def add_document(self, kb_id: str, name: str, content: bytes, content_type: str) -> Document:
        """添加文档到知识库"""
        try:
            # 查找知识库
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")
                
            # 创建文档对象
            doc = Document(
                id=str(uuid.uuid4()),
                knowledge_base_id=kb_id,
                name=name,
                content_type=content_type,
                size=len(content),
                chunk_count=0,
                status="processing",
                created_at=datetime.now()
            )
            
            # 保存文档
            # 在实际应用中，应该保存到PostgreSQL数据库和文件系统
            self.documents.append(doc)
            
            # 处理文档内容
            try:
                # 解码内容（假设是文本）
                text_content = content.decode('utf-8')
                
                # 分块处理文档
                chunks = await self._chunk_document(doc.id, kb_id, text_content)
                doc.chunk_count = len(chunks)
                doc.status = "processed"
                doc.updated_at = datetime.now()
                
                # 更新知识库文档计数和最后更新时间
                kb.document_count += 1
                kb.last_updated = datetime.now()
                
                logger.info(f"Added document: {doc.name} to knowledge base {kb.name} with {doc.chunk_count} chunks")
                
            except Exception as e:
                doc.status = "failed"
                doc.error = str(e)
                logger.error(f"Document processing error: {str(e)}", exc_info=True)
            
            return doc
            
        except Exception as e:
            logger.error(f"Add document error: {str(e)}", exc_info=True)
            raise
    
    async def get_documents(self, kb_id: str) -> List[Document]:
        """获取知识库中的所有文档"""
        try:
            # 在实际应用中，应该从PostgreSQL数据库查询
            return [doc for doc in self.documents if doc.knowledge_base_id == kb_id]
            
        except Exception as e:
            logger.error(f"Get documents error: {str(e)}", exc_info=True)
            raise
    
    async def delete_document(self, kb_id: str, document_id: str) -> bool:
        """从知识库中删除文档"""
        try:
            # 查找文档
            docs = [doc for doc in self.documents if doc.id == document_id and doc.knowledge_base_id == kb_id]
            if not docs:
                return False
                
            doc = docs[0]
            
            # 删除文档的所有分块
            self.chunks = [chunk for chunk in self.chunks if chunk.document_id != document_id]
            
            # 删除文档
            # 在实际应用中，应该从PostgreSQL数据库和文件系统删除
            self.documents = [d for d in self.documents if d.id != document_id]
            
            # 删除向量数据库中的向量
            await self.vector_service.delete_by_document(document_id)
            
            # 更新知识库文档计数和最后更新时间
            kb = await self.get_knowledge_base(kb_id)
            if kb:
                kb.document_count = max(0, kb.document_count - 1)
                kb.last_updated = datetime.now()
            
            logger.info(f"Deleted document: {doc.name} from knowledge base {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Delete document error: {str(e)}", exc_info=True)
            raise
    
    async def sync_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """同步知识库（重新处理和索引所有文档）"""
        try:
            # 查找知识库
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")
                
            # 获取知识库中的所有文档
            docs = await self.get_documents(kb_id)
            
            # 删除知识库中的所有向量
            await self.vector_service.delete_by_knowledge_base(kb_id)
            
            # 重新处理所有文档
            processed_documents = 0
            indexed_chunks = 0
            
            for doc in docs:
                # 重置文档状态
                doc.status = "processing"
                doc.chunk_count = 0
                doc.error = None
                
                try:
                    # 在实际应用中，应该从文件系统读取文档内容
                    # 这里为了演示，生成一些模拟内容
                    text_content = f"这是文档 {doc.name} 的内容。用于知识库检索测试。"
                    
                    # 删除文档的所有分块
                    self.chunks = [chunk for chunk in self.chunks if chunk.document_id != doc.id]
                    
                    # 重新分块处理文档
                    chunks = await self._chunk_document(doc.id, kb_id, text_content)
                    doc.chunk_count = len(chunks)
                    doc.status = "processed"
                    doc.updated_at = datetime.now()
                    
                    processed_documents += 1
                    indexed_chunks += doc.chunk_count
                    
                except Exception as e:
                    doc.status = "failed"
                    doc.error = str(e)
                    logger.error(f"Document reprocessing error: {str(e)}", exc_info=True)
            
            # 更新知识库最后更新时间
            kb.last_updated = datetime.now()
            
            logger.info(f"Synced knowledge base: {kb.name} - processed {processed_documents} documents with {indexed_chunks} chunks")
            
            return {
                "processed_documents": processed_documents,
                "indexed_chunks": indexed_chunks
            }
            
        except Exception as e:
            logger.error(f"Sync knowledge base error: {str(e)}", exc_info=True)
            raise
    
    async def _chunk_document(self, document_id: str, kb_id: str, content: str) -> List[Chunk]:
        """将文档内容分块"""
        # 使用父子块策略进行分块
        parent_size = settings.PARENT_BLOCK_SIZE
        child_size = settings.CHILD_BLOCK_SIZE
        overlap = settings.BLOCK_OVERLAP
        
        # 分割为父块
        parent_blocks = []
        for i in range(0, len(content), parent_size - overlap):
            parent_text = content[i:i + parent_size]
            if len(parent_text.strip()) > 0:
                parent_blocks.append(parent_text)
        
        # 为每个父块创建子块
        all_chunks = []
        for parent_idx, parent_text in enumerate(parent_blocks):
            # 创建父块
            parent_id = str(uuid.uuid4())
            parent_chunk = Chunk(
                id=parent_id,
                document_id=document_id,
                knowledge_base_id=kb_id,
                content=parent_text,
                chunk_type="parent",
                metadata={"index": parent_idx},
                created_at=datetime.now()
            )
            
            # 将父块添加到列表
            all_chunks.append(parent_chunk)
            
            # 为父块创建子块
            for j in range(0, len(parent_text), child_size - overlap):
                child_text = parent_text[j:j + child_size]
                if len(child_text.strip()) > 0:
                    child_chunk = Chunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        knowledge_base_id=kb_id,
                        content=child_text,
                        chunk_type="child",
                        parent_id=parent_id,
                        metadata={"parent_index": parent_idx, "index": j // (child_size - overlap)},
                        created_at=datetime.now()
                    )
                    
                    # 将子块添加到列表
                    all_chunks.append(child_chunk)
        
        # 保存分块
        # 在实际应用中，应该保存到PostgreSQL数据库
        self.chunks.extend(all_chunks)
        
        # 为每个块生成向量并索引
        await self._index_chunks(all_chunks)
        
        return all_chunks
    
    async def _index_chunks(self, chunks: List[Chunk]) -> None:
        """为分块生成向量并索引"""
        # 为每个块生成向量
        for chunk in chunks:
            # 生成向量
            vector = await self.vector_service.encode_text(chunk.content)
            chunk.vector = vector
            
            # 准备向量数据
            vector_data = {
                "id": chunk.id,
                "knowledge_base_id": chunk.knowledge_base_id,
                "document_id": chunk.document_id,
                "chunk_id": chunk.id,
                "chunk_type": chunk.chunk_type,
                "parent_id": chunk.parent_id,
                "title": "",  # 在实际应用中，应该提取标题
                "content": chunk.content,
                "vector": vector,
                "metadata": chunk.metadata,
                "created_at": chunk.created_at.isoformat()
            }
            
            # 插入向量数据库
            await self.vector_service.insert([vector_data])
            
            # 如果是父块，也添加到全文索引
            if chunk.chunk_type == "parent":
                await self.fulltext_service.index_document({
                    "id": chunk.id,
                    "knowledge_base_id": chunk.knowledge_base_id,
                    "document_id": chunk.document_id,
                    "title": "",  # 在实际应用中，应该提取标题
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "created_at": chunk.created_at
                })
    
    async def _create_mock_data(self) -> None:
        """创建模拟数据（仅用于演示）"""
        # 创建知识库
        kb1 = KnowledgeBase(
            id="kb1",
            name="产品文档",
            description="Dify产品相关文档",
            document_count=3,
            last_updated=datetime.now(),
            status="active",
            created_at=datetime.now()
        )
        
        kb2 = KnowledgeBase(
            id="kb2",
            name="技术文档",
            description="Dify技术相关文档",
            document_count=2,
            last_updated=datetime.now(),
            status="active",
            created_at=datetime.now()
        )
        
        # 添加知识库
        self.knowledge_bases = [kb1, kb2]
        
        # 创建文档
        doc1 = Document(
            id="doc1",
            knowledge_base_id="kb1",
            name="Dify知识库检索功能介绍.txt",
            content_type="text/plain",
            size=1024,
            chunk_count=5,
            status="processed",
            created_at=datetime.now()
        )
        
        doc2 = Document(
            id="doc2",
            knowledge_base_id="kb2",
            name="如何使用语义检索功能.txt",
            content_type="text/plain",
            size=2048,
            chunk_count=8,
            status="processed",
            created_at=datetime.now()
        )
        
        # 添加文档
        self.documents = [doc1, doc2]