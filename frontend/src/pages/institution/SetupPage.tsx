import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getInstitution,
  getSetupState,
  patchSetupStep,
  completeSetup,
  getDatasets,
} from '../../api/institutions'
import type { InstitutionSetupState, SetupStepPatch } from '../../types'
import Wordmark from '../../components/ui/Wordmark'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import ProgressRail from './setup/ProgressRail'
import ProfileStep from './setup/ProfileStep'
import ProgramStep from './setup/ProgramStep'
import DataStep from './setup/DataStep'
import TeamStep from './setup/TeamStep'
import CompleteSummary from './setup/CompleteSummary'

export default function SetupPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [currentStep, setCurrentStep] = useState<number | null>(null)

  const institutionQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution, retry: false })
  const setupQ = useQuery({ queryKey: ['institution-setup'], queryFn: getSetupState })
  const datasetsQ = useQuery({
    queryKey: ['institution-datasets'],
    queryFn: getDatasets,
    enabled: !!institutionQ.data,
  })

  const institution = institutionQ.data ?? null
  const setupState = setupQ.data
  const datasetCount = Array.isArray(datasetsQ.data) ? datasetsQ.data.length : 0

  // Resume at the persisted step the first time state loads (Spec 30 §2/§6).
  useEffect(() => {
    if (currentStep == null && setupState && !setupState.setup_complete) {
      setCurrentStep(typeof setupState.step === 'number' ? setupState.step : 1)
    }
  }, [setupState, currentStep])

  const patchStep = useMutation({
    mutationFn: (patch: SetupStepPatch) => patchSetupStep(patch),
    onSuccess: (state) => queryClient.setQueryData(['institution-setup'], state),
  })

  const finish = useMutation({
    mutationFn: completeSetup,
    onSuccess: (state) => {
      queryClient.setQueryData(['institution-setup'], state)
      queryClient.invalidateQueries({ queryKey: ['institution'] })
      showToast('Setup complete — welcome aboard 🎉', 'success')
      navigate('/i/dashboard')
    },
    onError: () =>
      showToast('Add your profile and a first program before finishing.', 'error'),
  })

  function goToStep(step: number, extra?: Omit<SetupStepPatch, 'step'>) {
    setCurrentStep(step)
    patchStep.mutate({ step: step as 1 | 2 | 3 | 4, ...extra })
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (setupQ.isLoading || (institutionQ.isLoading && !institutionQ.isError)) {
    return (
      <div className="mx-auto max-w-2xl space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    )
  }

  // ── Already complete → read-only summary (not forced) ───────────────────────
  if (setupState?.setup_complete) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <CompleteSummary institution={institution} setupState={setupState} />
      </div>
    )
  }

  const state = setupState as InstitutionSetupState
  const step = currentStep ?? 1
  const canSkipToDashboard = !!state?.steps_complete?.program

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-5 sm:p-6">
      {/* Header — wordmark + title + step counter (Spec 30 §3) */}
      <header className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Wordmark className="h-6 w-auto" />
            <h1 className="text-base font-semibold text-foreground sm:text-lg">
              Set up your institution
            </h1>
          </div>
          <span className="shrink-0 text-xs font-medium text-muted-foreground sm:text-sm">
            Step {step} of 4
          </span>
        </div>
        <ProgressRail current={step} stepsComplete={state.steps_complete} />
        {canSkipToDashboard && step < 4 && (
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => finish.mutate()}
              disabled={finish.isPending}
              className="text-xs font-medium text-secondary hover:underline disabled:opacity-50"
            >
              Skip to dashboard
            </button>
          </div>
        )}
      </header>

      {/* Active step */}
      {step === 1 && (
        <ProfileStep
          institution={institution}
          onSaved={() => goToStep(2, { mark_complete: { profile: true } })}
        />
      )}
      {step === 2 && (
        <ProgramStep
          onSaved={() => goToStep(3, { mark_complete: { program: true } })}
          onBack={() => goToStep(1)}
        />
      )}
      {step === 3 && (
        <DataStep
          datasetCount={datasetCount}
          onOpenUpload={() => navigate('/i/data')}
          onSkip={() => goToStep(4, { skip_data: true })}
          onContinue={() => goToStep(4)}
          onBack={() => goToStep(2)}
          busy={patchStep.isPending}
        />
      )}
      {step === 4 && (
        <TeamStep
          onFinish={() => finish.mutate()}
          onBack={() => goToStep(3)}
          finishing={finish.isPending}
        />
      )}
    </div>
  )
}
