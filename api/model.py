import os
import asyncio
import time
from loguru import logger
import config

clipModel = None
clipProcessor = None
siglipModel = None
siglipProcessor = None
modelsInitialized = {"clip": False, "siglip": False}

def _init_clip_model_sync():
    device = os.getenv("DEVICE", "cpu")
    logger.info("初始化CLIP模型, device: %s..." % (device))
    try:
        from transformers import AutoProcessor, AutoModel
        logger.info(f"开始下载CLIP模型: {config.CLIP_MODEL}")
        start_time = time.time()
        
        model = AutoModel.from_pretrained(config.CLIP_MODEL)
        logger.info(f"CLIP模型下载完成，耗时: {time.time() - start_time:.2f}秒")
        
        processor = AutoProcessor.from_pretrained(config.CLIP_MODEL)
        logger.info(f"CLIP处理器下载完成，耗时: {time.time() - start_time:.2f}秒")
        
        if device != "cpu":
            logger.info(f"将CLIP模型移动到设备: {device}")
            model = model.to(device)
        
        logger.info("CLIP模型初始化完成")
        return model, processor
    except Exception as e:
        logger.error(f"CLIP模型初始化失败: {str(e)}")
        raise

def _init_siglip_model_sync():
    device = os.getenv("DEVICE", "cpu")
    logger.info("初始化SigLIP模型, device: %s..." % (device))
    try:
        from transformers import AutoProcessor, AutoModel
        logger.info(f"开始下载SigLIP模型: {config.SIGLIP_MODEL}")
        start_time = time.time()
        
        model = AutoModel.from_pretrained(config.SIGLIP_MODEL)
        logger.info(f"SigLIP模型下载完成，耗时: {time.time() - start_time:.2f}秒")
        
        processor = AutoProcessor.from_pretrained(config.SIGLIP_MODEL)
        logger.info(f"SigLIP处理器下载完成，耗时: {time.time() - start_time:.2f}秒")
        
        if device != "cpu":
            logger.info(f"将SigLIP模型移动到设备: {device}")
            model = model.to(device)
        
        logger.info("SigLIP模型初始化完成")
        return model, processor
    except Exception as e:
        logger.error(f"SigLIP模型初始化失败: {str(e)}")
        raise

async def init_model():
    global clipModel, clipProcessor, siglipModel, siglipProcessor, modelsInitialized
    supportedModels = config.SUPPORTED_MODELS.lower()
    logger.info(f"准备初始化模型: {supportedModels}")
    
    # 检查网络连接
    if config.MODEL_DEBUG:
        try:
            import urllib.request
            logger.info("检查网络连接...")
            urllib.request.urlopen('https://huggingface.co', timeout=10)
            logger.info("网络连接正常")
        except Exception as e:
            logger.warning(f"网络连接检查失败: {str(e)}")
    
    # 兼容 Python 3.8 的线程执行方式
    loop = asyncio.get_event_loop()
    
    try:
        if supportedModels in ["clip", "all"]:
            if not modelsInitialized["clip"]:
                logger.info("开始初始化CLIP模型...")
                clipModel, clipProcessor = await asyncio.wait_for(
                    loop.run_in_executor(None, _init_clip_model_sync),
                    timeout=config.MODEL_INIT_TIMEOUT  # 使用配置的超时时间
                )
                modelsInitialized["clip"] = True
                logger.info("CLIP模型初始化成功")
        
        if supportedModels in ["siglip", "all"]:
            if not modelsInitialized["siglip"]:
                logger.info("开始初始化SigLIP模型...")
                siglipModel, siglipProcessor = await asyncio.wait_for(
                    loop.run_in_executor(None, _init_siglip_model_sync),
                    timeout=config.MODEL_INIT_TIMEOUT  # 使用配置的超时时间
                )
                modelsInitialized["siglip"] = True
                logger.info("SigLIP模型初始化成功")
        
        logger.info(f"模型初始化状态: {modelsInitialized}")
        
    except asyncio.TimeoutError:
        logger.error("模型初始化超时，请检查网络连接或增加超时时间")
        raise
    except Exception as e:
        logger.error(f"模型初始化过程中发生错误: {str(e)}")
        raise

def is_model_ready(modelType=None):
    global modelsInitialized
    if modelType is None:
        return any(modelsInitialized.values())
    return modelsInitialized.get(modelType.lower(), False)

def get_clip_model():
    global clipModel
    if clipModel is None:
        raise RuntimeError("CLIP模型未初始化")
    return clipModel

def get_clip_processor():
    global clipProcessor
    if clipProcessor is None:
        raise RuntimeError("CLIP处理器未初始化")
    return clipProcessor

def get_siglip_model():
    global siglipModel
    if siglipModel is None:
        raise RuntimeError("SigLIP模型未初始化")
    return siglipModel

def get_siglip_processor():
    global siglipProcessor
    if siglipProcessor is None:
        raise RuntimeError("SigLIP处理器未初始化")
    return siglipProcessor

def get_supported_models():
    return config.SUPPORTED_MODELS.lower()

def get_model_type():
    supported = get_supported_models()
    if supported == "all":
        return "clip"
    return supported

def emb_result_wrapper(embedding):
    import numpy as np
    if hasattr(embedding, 'cpu'):
        embedding = embedding.cpu().numpy()
    if hasattr(embedding, 'flatten'):
        embedding = embedding.flatten()
    embedding = [round(float(v), 6) for v in embedding]
    return embedding

def encode_image_clip(img):
    import torch
    model = get_clip_model()
    processor = get_clip_processor()
    inputs = processor(images=img, return_tensors="pt")
    device = os.getenv("DEVICE", "cpu")
    if device != "cpu":
        inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        outputs = outputs / outputs.norm(dim=-1, keepdim=True)
    return emb_result_wrapper(outputs[0])

def encode_image_siglip(img):
    import torch
    model = get_siglip_model()
    processor = get_siglip_processor()
    inputs = processor(images=img, return_tensors="pt")
    device = os.getenv("DEVICE", "cpu")
    if device != "cpu":
        inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        outputs = outputs / outputs.norm(dim=-1, keepdim=True)
    return emb_result_wrapper(outputs[0])

def encode_image(img, modelType=None):
    if modelType is None:
        modelType = get_model_type()
    modelType = modelType.lower()
    if modelType == "siglip":
        if not is_model_ready("siglip"):
            raise RuntimeError("SigLIP模型未初始化")
        return encode_image_siglip(img)
    elif modelType == "clip":
        if not is_model_ready("clip"):
            raise RuntimeError("CLIP模型未初始化")
        return encode_image_clip(img)
    else:
        raise ValueError(f"不支持的模型类型: {modelType}")

def encode_image_all(img):
    result = {}
    if is_model_ready("clip"):
        result["clip"] = encode_image_clip(img)
    if is_model_ready("siglip"):
        result["siglip"] = encode_image_siglip(img)
    return result

def encode_text(text):
    import torch
    model = get_clip_model()
    processor = get_clip_processor()
    inputs = processor(text=text, return_tensors="pt", padding=True, truncation=True)
    device = os.getenv("DEVICE", "cpu")
    if device != "cpu":
        inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.get_text_features(**inputs)
        outputs = outputs / outputs.norm(dim=-1, keepdim=True)
    return emb_result_wrapper(outputs[0])