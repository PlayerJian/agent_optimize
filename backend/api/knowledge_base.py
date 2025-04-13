from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from services.knowledge_base_service import KnowledgeBaseService
from models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, Document

router = APIRouter()
logger = logging.getLogger("retrieval")

# 获取服务实例
def get_kb_service():
    return KnowledgeBaseService()

@router.get("/", response_model=List[KnowledgeBase])
async def get_knowledge_bases(
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """获取所有知识库"""
    try:
        return await kb_service.get_all_knowledge_bases()
    except Exception as e:
        logger.error(f"Get knowledge bases error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取知识库失败: {str(e)}")

@router.get("/{kb_id}", response_model=KnowledgeBase)
async def get_knowledge_base(
    kb_id: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """获取特定知识库"""
    try:
        kb = await kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
        return kb
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取知识库失败: {str(e)}")

@router.post("/", response_model=KnowledgeBase)
async def create_knowledge_base(
    kb_create: KnowledgeBaseCreate,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """创建新知识库"""
    try:
        return await kb_service.create_knowledge_base(kb_create)
    except Exception as e:
        logger.error(f"Create knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")

@router.put("/{kb_id}", response_model=KnowledgeBase)
async def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """更新知识库"""
    try:
        kb = await kb_service.update_knowledge_base(kb_id, kb_update)
        if not kb:
            raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
        return kb
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新知识库失败: {str(e)}")

@router.delete("/{kb_id}", response_model=Dict[str, Any])
async def delete_knowledge_base(
    kb_id: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """删除知识库"""
    try:
        success = await kb_service.delete_knowledge_base(kb_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
        return {"success": True, "message": f"知识库 {kb_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")

@router.post("/{kb_id}/documents", response_model=Document)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    document_name: str = Form(None),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """上传文档到知识库"""
    try:
        # 如果没有提供文档名称，使用上传的文件名
        if not document_name:
            document_name = file.filename
            
        content = await file.read()
        document = await kb_service.add_document(kb_id, document_name, content, file.content_type)
        return document
    except Exception as e:
        logger.error(f"Upload document error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传文档失败: {str(e)}")

@router.get("/{kb_id}/documents", response_model=List[Document])
async def get_documents(
    kb_id: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """获取知识库中的所有文档"""
    try:
        return await kb_service.get_documents(kb_id)
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")

@router.delete("/{kb_id}/documents/{document_id}", response_model=Dict[str, Any])
async def delete_document(
    kb_id: str,
    document_id: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """从知识库中删除文档"""
    try:
        success = await kb_service.delete_document(kb_id, document_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"文档 {document_id} 不存在")
        return {"success": True, "message": f"文档 {document_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

@router.post("/{kb_id}/sync", response_model=Dict[str, Any])
async def sync_knowledge_base(
    kb_id: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """同步知识库（重新处理和索引所有文档）"""
    try:
        result = await kb_service.sync_knowledge_base(kb_id)
        return {
            "success": True, 
            "message": f"知识库 {kb_id} 同步完成",
            "processed_documents": result.get("processed_documents", 0),
            "indexed_chunks": result.get("indexed_chunks", 0)
        }
    except Exception as e:
        logger.error(f"Sync knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"同步知识库失败: {str(e)}")