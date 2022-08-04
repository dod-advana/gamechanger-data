from os import listdir, remove
from os.path import join, exists
from threading import current_thread
from gamechangerml.api.utils import processmanager
from gamechangerml.src.utilities import configure_logger


def delete_local_corpus(corpus_dir="corpus", logger=None):
    """Delete corpus files and manage this process with processmanager 
    from gamechangerml.api.utils.

    Args:
        corpus_dir (str, optional): Directory containing corpus files. Defaults 
            to "corpus".
        logger (logging.Logger or None, optional): If None, uses 
            configure_logger(). Default is None.
    
    Returns:
        int: True if success, False if exception.
    """
    if logger is None:
        logger = configure_logger()

    try:
        if exists(corpus_dir):
            existing_files = listdir(corpus_dir)
            total = len(existing_files)

            if total > 0:
                # Initialize progress
                processmanager.update_status(
                    processmanager.delete_corpus,
                    total,
                    len(existing_files),
                    thread_id=current_thread().ident,
                )

                logger.info("Removing existing corpus files.")
                completed = 1
                for file in existing_files:
                    remove(join(corpus_dir, file))
                    # Update progress
                    processmanager.update_status(
                        processmanager.delete_corpus,
                        completed,
                        total,
                        current_thread().ident,
                    )
                    completed += 1
    except Exception:
        logger.exception("Failed to delete local corpus.")
        processmanager.update_status(
            processmanager.delete_corpus,
            failed=True,
            thread_id=current_thread().ident,
        )
        return False
    else:
        return True
