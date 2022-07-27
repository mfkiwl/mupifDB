import importlib
import sys
import os

# os.environ["MUPIF_LOG_LEVEL"] = "INFO"
# os.environ["MUPIF_LOG_FILE"] = "mupif.log"

import logging
import argparse
import mupifDB
import mupif as mp




api_type = os.environ.get('MUPIFDB_REST_SERVER_TYPE', "mupif")
print(api_type)

log = logging.getLogger()
log.info('Execution script started')

daemon=mp.pyroutil.getDaemon()
logUri=str(daemon.register(mp.pyrolog.PyroLogReceiver()))

if __name__ == "__main__":
    workflow = None

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-eid', '--executionID', required=True, dest="id")
        args = parser.parse_args()
        weid = args.id

        execution_record = mupifDB.restApiControl.getExecutionRecord(weid)
        if execution_record is None:
            print("Execution not found")
            log.info("Execution not found")
            exit(1)

        workflow_record = mupifDB.restApiControl.getWorkflowRecordGeneral(execution_record["WorkflowID"], execution_record["WorkflowVersion"])
        if workflow_record is None:
            print("Workflow not found")
            log.info("Workflow not found")
            exit(1)

        #
        moduleImport = importlib.import_module(workflow_record["modulename"])
        print(moduleImport)
        workflow_class = getattr(moduleImport, workflow_record["classname"])
        #

        workflow = workflow_class()
        workflow.initialize(metadata={'Execution': {'ID': weid, 'Use_case_ID': workflow_record["UseCase"], 'Task_ID': execution_record["Task_ID"], 'Log_URI': logUri}})
        mupifDB.workflowmanager.mapInputs(workflow, args.id)
        workflow.solve()
        mupifDB.workflowmanager.mapOutputs(workflow, args.id, workflow.getExecutionTargetTime())
        workflow.terminate()

    except Exception as err:
        log.exception(err)
        try:
            workflow.terminate()
        except:
            pass
        if type(err) == mp.JobManNoResourcesException:
            print("Not enough resources")
            log.error('Not enough resources')
            sys.exit(2)
        sys.exit(1)

    except:
        print("Unknown error")
        log.info("Unknown error")
        if workflow is not None:
            workflow.terminate()
        sys.exit(1)

    sys.exit(0)
