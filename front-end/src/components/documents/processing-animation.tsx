"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Sparkles,
  Scissors,
  Cpu,
  Database,
  CheckCircle,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  ProcessingStage,
  PROCESSING_STAGES,
  getStageIndex,
  isStageComplete,
  isStageActive,
} from "@/lib/api/rag-documents";

interface ProcessingAnimationProps {
  currentStage: ProcessingStage;
  progress: number;
  message?: string;
  error?: string | null;
}

const stageIcons: Record<string, React.ElementType> = {
  extracting: FileText,
  cleaning: Sparkles,
  chunking: Scissors,
  embedding: Cpu,
  storing: Database,
  ready: CheckCircle,
};

export function ProcessingAnimation({
  currentStage,
  progress,
  message,
  error,
}: ProcessingAnimationProps) {
  const currentIndex = getStageIndex(currentStage);

  return (
    <div className="w-full py-8">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-neutral-700">
            Processing Documents
          </span>
          <span className="text-sm font-medium text-primary-600">
            {progress}%
          </span>
        </div>
        <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Stage Cards */}
      <div className="flex flex-wrap justify-center gap-4">
        {PROCESSING_STAGES.map((stage, index) => {
          const Icon = stageIcons[stage.key] || FileText;
          const isComplete = isStageComplete(stage.key, currentStage);
          const isActive = isStageActive(stage.key, currentStage);
          const isPending = !isComplete && !isActive;
          const isError = currentStage === "error" && isActive;

          return (
            <motion.div
              key={stage.key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.4 }}
              className="relative"
            >
              {/* Connector Line */}
              {index < PROCESSING_STAGES.length - 1 && (
                <div className="hidden md:block absolute top-1/2 left-full w-4 h-0.5 -translate-y-1/2">
                  <motion.div
                    className={`h-full rounded-full ${
                      isComplete ? "bg-green-500" : "bg-neutral-300"
                    }`}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: isComplete ? 1 : 0 }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              )}

              {/* Stage Card */}
              <motion.div
                className={`
                  relative flex flex-col items-center p-4 rounded-xl border-2 min-w-[100px]
                  transition-colors duration-300
                  ${
                    isComplete
                      ? "border-green-500 bg-green-50"
                      : isActive
                        ? "border-primary-500 bg-primary-50"
                        : isError
                          ? "border-red-500 bg-red-50"
                          : "border-neutral-200 bg-white"
                  }
                `}
                animate={
                  isActive && !isError
                    ? {
                        boxShadow: [
                          "0 0 0 0 rgba(26, 54, 93, 0)",
                          "0 0 0 8px rgba(26, 54, 93, 0.1)",
                          "0 0 0 0 rgba(26, 54, 93, 0)",
                        ],
                      }
                    : {}
                }
                transition={{
                  duration: 1.5,
                  repeat: isActive && !isError ? Infinity : 0,
                  ease: "easeInOut",
                }}
              >
                {/* Icon */}
                <div
                  className={`
                  w-12 h-12 rounded-full flex items-center justify-center mb-2
                  ${
                    isComplete
                      ? "bg-green-500 text-white"
                      : isActive
                        ? "bg-primary-500 text-white"
                        : isError
                          ? "bg-red-500 text-white"
                          : "bg-neutral-100 text-neutral-400"
                  }
                `}
                >
                  <AnimatePresence mode="wait">
                    {isComplete ? (
                      <motion.div
                        key="complete"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      >
                        <CheckCircle className="w-6 h-6" />
                      </motion.div>
                    ) : isActive && !isError ? (
                      <motion.div
                        key="active"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      >
                        <Loader2 className="w-6 h-6" />
                      </motion.div>
                    ) : isError ? (
                      <motion.div
                        key="error"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                      >
                        <AlertCircle className="w-6 h-6" />
                      </motion.div>
                    ) : (
                      <Icon className="w-6 h-6" />
                    )}
                  </AnimatePresence>
                </div>

                {/* Label */}
                <span
                  className={`
                  text-sm font-medium
                  ${
                    isComplete
                      ? "text-green-700"
                      : isActive
                        ? "text-primary-700"
                        : isError
                          ? "text-red-700"
                          : "text-neutral-400"
                  }
                `}
                >
                  {stage.label}
                </span>

                {/* Description (shown on active) */}
                <AnimatePresence>
                  {isActive && !isError && (
                    <motion.span
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="text-xs text-primary-600 mt-1 text-center"
                    >
                      {stage.description}
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.div>
          );
        })}
      </div>

      {/* Status Message */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6 text-center"
          >
            <p className="text-sm text-neutral-600">{message}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
          >
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ready State */}
      <AnimatePresence>
        {currentStage === "ready" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-8 text-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-6 py-3 bg-green-500 text-white rounded-full font-medium"
            >
              <CheckCircle className="w-5 h-5" />
              Ready to answer questions!
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ProcessingAnimation;
