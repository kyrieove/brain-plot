% Regenerates the REAL EEGLAB-authored epoched .set fixtures used by test_erp_plot.py (needs MATLAB + EEGLAB).
% Source: EEGLAB's own sample_data/eeglab_data.set (32 channels, 128 Hz, events 'square' and 'rt').
% Pipeline, all recorded by EEGLAB in EEG.history: band-pass 0.1-30 Hz, average reference, epoch -0.2..0.8 s
% around BOTH event types (so an epoch can hold two events: the lock event at latency 0 and a neighbour),
% remove baseline -200..0 ms, keep 20 random trials per "subject".
% Run: matlab -batch "run('make_eeglab_fixture.m')"   (edit eeglabRoot first)
eeglabRoot = 'D:\1\application\eeglab\eeglab2025.0.0';
outRoot    = fullfile(fileparts(mfilename('fullpath')), 'eeglab');

addpath(eeglabRoot);
eeglab nogui;

raw = pop_loadset('filename', 'eeglab_data.set', 'filepath', fullfile(eeglabRoot, 'sample_data'));
raw = pop_eegfiltnew(raw, 'locutoff', 0.1, 'hicutoff', 30);
raw = pop_reref(raw, []);
base = pop_epoch(raw, {'square', 'rt'}, [-0.2 0.8]);
base = pop_rmbase(base, [-200 0]);

groups = {'G1', 'G2'};
subjects = {{'sub01', 'sub02'}, {'sub03', 'sub04'}};
rng(1);
fid = fopen(fullfile(outRoot, 'counts.csv'), 'w');
fprintf(fid, 'subject,type_at_latency_0,n_epochs\n');
for g = 1:2
    gdir = fullfile(outRoot, groups{g});
    if ~exist(gdir, 'dir'), mkdir(gdir); end
    for s = 1:2
        keep = sort(randperm(base.trials, 20));
        sub = pop_select(base, 'trial', keep);
        sub.setname = subjects{g}{s};
        % sub02 is saved as .set + .fdt (the EEGLAB default for large data), the others as one .set file
        if g == 1 && s == 2
            pop_saveset(sub, 'filename', [subjects{g}{s} '.set'], 'filepath', gdir, 'savemode', 'twofiles');
        else
            pop_saveset(sub, 'filename', [subjects{g}{s} '.set'], 'filepath', gdir, 'savemode', 'onefile');
        end
        lock = cell(1, sub.trials);
        for t = 1:sub.trials
            et = sub.epoch(t).eventtype;
            el = cell2mat(sub.epoch(t).eventlatency);
            if ~iscell(et), et = {et}; end
            [~, i0] = min(abs(el));
            lock{t} = et{i0};
        end
        for ty = {'rt', 'square'}
            fprintf(fid, '%s,%s,%d\n', subjects{g}{s}, ty{1}, sum(strcmp(lock, ty{1})));
        end
    end
end
fclose(fid);
disp('DONE');
