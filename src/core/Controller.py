import os
import importlib
from config import APP_PATH
import abc #Module provides the infrastructure for defining abstract base classes


"""
    Responsible for the communication between views and models in addiction to
    being responsible for the behavior of the program.
"""
class Controller(metaclass=abc.ABCMeta):
    #-----------------------------------------------------------------------
    #        Methods
    #-----------------------------------------------------------------------
    """
        Executes controller and associated view with it.
    """
    @abc.abstractmethod
    def main(self):
        return
    
    """
        Given a view name, return an instance of it
    
        @param viewName:string View to be opened
    """
    def loadView(self, viewName):
        response = None
        
        # Set view name
        viewName = viewName[0].upper()+viewName[1:]+"View"
        # Check if file exists
        if os.path.exists(APP_PATH+"/views/"+viewName+".py"):
            module = importlib.import_module("views."+viewName)
            class_ = getattr(module, viewName)
            response = class_(self)
        
        return response
    
    """
        @description Given a model name, return an instance of it
        @author Andrés Gómez
        @paran modelName: string Model to be opened
    """
    def loadModel(self, modelName):
        response = None
        
        # Set view name
        modelName = modelName[0].upper()+modelName[1:]+"Model"
        
        # Check if file exists
        if os.path.exists(APP_PATH+"/models/"+modelName+".py"):
            module = importlib.import_module("models."+modelName)
            class_ = getattr(module, modelName)
            response = class_(self)
        
        return response
        
        
    