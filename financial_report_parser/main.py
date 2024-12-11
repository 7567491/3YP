import os
from pathlib import Path
from config.settings import *
from src.pdf_processor import PDFProcessor
from src.llm_processor import LLMProcessor
from src.data_storage import DataStorage
from src.utils import setup_logging, ProcessTracker, stream_output

def main():
    # 使用配置中的日志文件路径
    logger = setup_logging(LOG_FILE)
    
    # 初始化进度跟踪器
    tracker = ProcessTracker(DATA_DIR / "process_state.json")
    
    try:
        # 初始化各个组件
        pdf_processor = PDFProcessor(chunk_size=PDF_CHUNK_SIZE)
        llm_processor = LLMProcessor(
            api_key=API_KEY,
            api_base=API_BASE,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE
        )
        data_storage = DataStorage(db_path=DB_PATH)

        # 处理2023年报
        pdf_path = ANNUAL_REPORTS_DIR / "2023年报.pdf"
        json_path = ANNUAL_REPORTS_DIR / "2023.json"
        year = 2023

        # 1. 提取PDF文本
        if not tracker.state.get('extracted_text'):
            logger.info("正在提取PDF文本...")
            text = pdf_processor.extract_text(pdf_path)
            tracker.state['extracted_text'] = text
            tracker.save_state()
        else:
            logger.info("使用已提取的文本...")
            text = tracker.state['extracted_text']

        # 2. 分块处理文本
        logger.info("正在处理文本...")
        all_data = tracker.state.get('results', {})
        
        for i, chunk in enumerate(pdf_processor.split_text(text)):
            if tracker.is_chunk_processed(i):
                logger.info(f"跳过已处理的文本块 {i+1}")
                continue
                
            logger.info(f"正在处理第{i+1}个文本块...")
            chunk_data = llm_processor.process_chunk(chunk)
            all_data.update(chunk_data)
            
            # 保存进度
            tracker.save_chunk_result(i, chunk_data)
            
            # 实时保存数据
            data_storage.save_json(all_data, json_path)

        # 3. 保存数据到数据库
        logger.info("正在保存数据到数据库...")
        data_storage.save_to_db(all_data, year)

        logger.info("处理完成！")

    except Exception as e:
        logger.error(f"处理过程中出现错误: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
