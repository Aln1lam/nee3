"""

Neepu ä¸­é´ä»¶æ¨¡ååå?



å°åå§ç middleware.py æåä¸?6 ä¸ªç¬ç«æ¨¡å?

1. rate_limiting  - éçéå¶

2. logging        - è¯·æ±æ¥å¿

3. compression    - ååºåç¼©  

4. security       - å®å¨å¤?

5. caching        - ç¼å­æ§å¶

6. error_handling - éè¯¯å¤ç



ãä½¿ç¨ç¤ºä¾ã?



# æ¹å¼ 1: ä»åå¯¼å¥

from backend.middleware_refactored import (

    rate_limit,

    submission_rate_limit,

    RequestLogger,

)



# æ¹å¼ 2: ä»å­æ¨¡åå¯¼å¥  

from backend.middleware_refactored.rate_limiting import rate_limit

from backend.middleware_refactored.logging import RequestLogger



# æ¹å¼ 3: å?Flask åºç¨ä¸­åå§åï¼æ¨èï¼

from backend.middleware_refactored import init_all_middleware



app = Flask(__name__)

init_all_middleware(app)

"""



import logging as _logging



# ==================== Rate Limiting ====================

from .rate_limiting import (

    RateLimiter,

    rate_limiter,

    rate_limit,

    submission_rate_limit,

    login_rate_limit,

    TokenBucketStrategy,

)



# ==================== Logging ====================

from .logging import (

    RequestLogger,

)



# ==================== Compression ====================

from .compression import (

    GzipCompressor,

    register_gzip_compression,

    get_compression_stats,

)



# ==================== Security ====================

from .security import (

    SecurityHeaderManager,

    register_security_headers,

    add_hsts_header,

    remove_header,

)



# ==================== Caching ====================

from .caching import (

    CacheHeaderManager,

    no_cache,

    set_cache_headers,

    get_cache_expiration_time,

)



# ==================== Error Handling ====================

from .error_handling import (

    ErrorHandler,

    register_error_handlers,

    make_error_response,

)



__all__ = [

    # Rate Limiting

    'RateLimiter',

    'rate_limiter',

    'rate_limit',

    'submission_rate_limit',

    'login_rate_limit',

    'TokenBucketStrategy',

    

    # Logging

    'RequestLogger',

    

    # Compression

    'GzipCompressor',

    'register_gzip_compression',

    'get_compression_stats',

    

    # Security

    'SecurityHeaderManager',

    'register_security_headers',

    'add_hsts_header',

    'remove_header',

    

    # Caching

    'CacheHeaderManager',

    'no_cache',

    'set_cache_headers',

    'get_cache_expiration_time',

    

    # Error Handling

    'ErrorHandler',

    'register_error_handlers',

    'make_error_response',

    

    # Init function

    'init_all_middleware',

]



logger = _logging.getLogger(__name__)





def init_all_middleware(app, enable_compression: bool = True, security_policy: str = 'moderate') -> None:

    """

    åå§åææä¸­é´ä»¶

    

    è¿ä¸ªå½æ°åºè¯¥å?Flask åºç¨åå»ºåç«å³è°ç?

    

    Args:

        app: Flask åºç¨å®ä¾

        enable_compression: æ¯å¦å¯ç¨ååºåç¼©ï¼é»è®?Trueï¼?

        security_policy: å®å¨ç­ç¥çº§å« ('strict', 'moderate', 'permissive', é»è®¤ 'moderate')

    

    ä½¿ç¨ç¤ºä¾:

        from flask import Flask

        from backend.middleware_refactored import init_all_middleware

        

        app = Flask(__name__)

        

        # ä½¿ç¨é»è®¤éç½®

        init_all_middleware(app)

        

        # æèªå®ä¹éç½®

        init_all_middleware(

            app,

            enable_compression=True,

            security_policy='strict'

        )

        

        @app.route('/api/data')

        def get_data():

            return {'data': 'example'}

    

    æ­¤åï¼ææä¸­é´ä»¶åè½å°èªå¨å¯ç?

    â?è¯·æ±æ¥å¿è®°å½

    â?å®å¨å¤´æ·»å ï¼XSS/MIME/ç¹å»å«æé²æ¤ï¼?

    â?ç¼å­æ§å¶ï¼ETag/Cache-Controlï¼?

    â?ååºåç¼©ï¼Gzipï¼?

    â?éè¯¯ç»ä¸å¤ç

    â?éçéå¶è£é¥°å¨å¯ç?

    """

    

    # 1. éè¯¯å¤çï¼å¿é¡»é¦åæ³¨åï¼ä»¥ä¾¿æè·å¶ä»ä¸­é´ä»¶çéè¯¯ï¼?

    register_error_handlers(app)

    logger.info("â?Error handling registered")

    

    # 2. è¯·æ±æ¥å¿

    app.before_request(RequestLogger.log_request)

    app.after_request(RequestLogger.log_response)

    logger.info("â?Request logging enabled")

    

    # 3. å®å¨å¤?

    register_security_headers(app, policy_level=security_policy)

    logger.info(f"â?Security headers enabled (policy: {security_policy})")

    

    # 4. ååºåç¼©ï¼å¯éï¼

    if enable_compression:

        register_gzip_compression(app)

        logger.info("[✓] Response compression enabled")

    else:

        logger.info("[✓] Response compression disabled")

    

    logger.info("=" * 50)

    logger.info("All middleware initialized successfully!")

    logger.info("=" * 50)

    logger.info(f"  Rate limiting: Available via @rate_limit decorator")

    logger.info(f"  Logging: Automatic for all requests")

    logger.info(f"  Security: {security_policy.upper()} CSP policy applied")

    logger.info(f"  Compression: {'Enabled' if enable_compression else 'Disabled'}")

    logger.info(f"  Caching: Available via @no_cache or @set_cache_headers")

    logger.info(f"  Error handling: Automatic for all errors")

    logger.info("=" * 50)





