# encoding: utf-8
#
# Copyright (c) 2017 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-12-22
#

"""Generate CSL citations."""

from __future__ import print_function, absolute_import

import json
import logging
import os
import subprocess  # nosec
from tempfile import NamedTemporaryFile

from .locales import LOCALE_DIR


log = logging.getLogger(__name__)

# Ruby executable that generates the citation
PROG = os.path.join(os.path.dirname(__file__), 'cite')


class CitationError(Exception):
    """Raised if call to ``cite`` program fails."""


def generate(csldata, cslfile, bibliography=False, locale=None):
    """Generate an HTML & RTF citation for ``csldata`` using ``cslfile``."""
    import time
    start_time = time.time()
    
    with NamedTemporaryFile(suffix='.json',mode="w+") as fp:
        
        #log.debug(csldata)
        #log.debug(cslfile)
        json.dump(csldata, fp)
        fp.flush()

        cmd = [PROG, '--locale-dir', LOCALE_DIR]
        if bibliography:
            cmd.append('--bibliography')
        if locale:
            cmd += ['--locale', locale]

        cmd += [cslfile, fp.name]

        log.debug('[cite] cmd=%r', cmd)

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,  # nosec
                                 stderr=subprocess.PIPE)

            # Add timeout to prevent runaway loops (10 seconds should be enough for normal citations)
            stdout, stderr = p.communicate(timeout=10)
            
            if p.returncode:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else 'Unknown error'
                log.error('[cite] cite process failed with return code %d: %s', p.returncode, error_msg)
                
                # Check for specific known errors and provide better error messages
                if 'page_mangler' in error_msg:
                    raise CitationError('CSL engine error: page_mangler function not found. This citation style may be incompatible with the current CSL engine version.')
                elif 'execution error' in error_msg:
                    raise CitationError('CSL engine execution error. The citation style or reference data may be malformed.')
                else:
                    raise CitationError('cite exited with %d: %s', p.returncode, error_msg)

        except subprocess.TimeoutExpired:
            log.error('[cite] cite process timed out after 10 seconds - killing process')
            p.kill()
            stdout, stderr = p.communicate()
            raise CitationError('cite process timed out - possible runaway loop or malformed data')
        except Exception as e:
            log.error('[cite] unexpected error running cite process: %s', str(e))
            raise CitationError('cite process failed: %s', str(e))

    try:
        data = json.loads(stdout)
        html = data['html']

        log.debug('[cite] html=%r', html)

        rtf = '{\\rtf1\\ansi\\deff0 ' + data['rtf'] + '}'
        log.debug('[cite] rtf=%r', rtf)
        
        elapsed = time.time() - start_time
        log.debug('[cite] citation generation completed in %.3f seconds', elapsed)

        return dict(html=html, text=html, rtf=rtf)
    except (json.JSONDecodeError, KeyError) as e:
        log.error('[cite] failed to parse cite output: %s', str(e))
        log.error('[cite] stdout: %s', stdout.decode('utf-8', errors='ignore')[:500])
        raise CitationError('failed to parse cite output: %s', str(e))
