// Helper function to group tasks into user-friendly "rules"
export const groupTasksIntoRules = (tasks) => {
  const rules = [];
  const processedTaskIds = new Set();
  
  for (const task of tasks) {
    if (processedTaskIds.has(task.id)) continue;
    
    const { service, params, hour, minute, days_of_week } = task;
    const groupId = params?.group_id;
    
    if (!groupId) {
      // Single task without group - show as individual task
      const isInterval = task.task_type === 'interval';
      rules.push({
        id: `single_${task.id}`,
        type: service === 'agh' ? 'content' : 'bandwidth',
        groupId,
        service,
        task: task.task,
        startTime: isInterval ? null : `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
        endTime: null,
        days: days_of_week || [0,1,2,3,4,5,6],
        taskIds: [task.id],
        enabled: task.enabled,
        params: task.params,
        isInterval,
        intervalMinutes: task.interval_minutes
      });
      processedTaskIds.add(task.id);
      continue;
    }
    
    // Look for paired task (activate/deactivate or apply/remove)
    let pairedTask = null;
    
    if (service === 'agh') {
      // Content blocking: look for set_devices_rules + clear_devices_rules pair
      if (task.task === 'set_devices_rules') {
        // This is a start task, look for its end task
        pairedTask = tasks.find(t => 
          !processedTaskIds.has(t.id) &&
          t.service === 'agh' && 
          t.task === 'clear_devices_rules' &&
          t.params?.group_id === groupId
        );
      } else if (task.task === 'clear_devices_rules') {
        // This is an end task, look for its start task
        pairedTask = tasks.find(t => 
          !processedTaskIds.has(t.id) &&
          t.service === 'agh' && 
          t.task === 'set_devices_rules' &&
          t.params?.group_id === groupId
        );
      }
    } else if (service === 'bandwidth') {
      // Bandwidth limiting: look for apply_group_limits + delete_group_limits pair
      if (task.task === 'apply_group_limits') {
        // This is a start task, look for its end task
        pairedTask = tasks.find(t => 
          !processedTaskIds.has(t.id) &&
          t.service === 'bandwidth' && 
          t.task === 'delete_group_limits' &&
          t.params?.group_id === groupId
        );
      } else if (task.task === 'delete_group_limits') {
        // This is an end task, look for its start task
        pairedTask = tasks.find(t => 
          !processedTaskIds.has(t.id) &&
          t.service === 'bandwidth' && 
          t.task === 'apply_group_limits' &&
          t.params?.group_id === groupId
        );
      }
    }
    
    if (pairedTask) {
      // Found a pair - create a rule
      // Determine start and end tasks based on task type, not time
      let startTask, endTask;
      
      if (service === 'agh') {
        // For content blocking: set_devices_rules = start, clear_devices_rules = end
        if (task.task === 'set_devices_rules') {
          startTask = task;
          endTask = pairedTask;
        } else {
          startTask = pairedTask;
          endTask = task;
        }
      } else if (service === 'bandwidth') {
        // For bandwidth: apply_group_limits = start, delete_group_limits = end
        if (task.task === 'apply_group_limits') {
          startTask = task;
          endTask = pairedTask;
        } else {
          startTask = pairedTask;
          endTask = task;
        }
      }
      
      // Check if rule spans midnight (start time > end time)
      const startHour = startTask.hour;
      const startMin = startTask.minute;
      const endHour = endTask.hour;
      const endMin = endTask.minute;
      const spansMidnight = startHour > endHour || (startHour === endHour && startMin > endMin);
      
      // For display purposes, show the original days from the start task
      // The end task days are already adjusted during creation if spanning midnight
      const displayDays = startTask.days_of_week || [0,1,2,3,4,5,6];
      
      // Create a unique rule ID that's consistent regardless of which task we encounter first
      const ruleId = `rule_${Math.min(task.id, pairedTask.id)}_${Math.max(task.id, pairedTask.id)}`;
      
      rules.push({
        id: ruleId,
        type: service === 'agh' ? 'content' : 'bandwidth',
        groupId,
        service,
        startTime: `${startTask.hour.toString().padStart(2, '0')}:${startTask.minute.toString().padStart(2, '0')}`,
        endTime: `${endTask.hour.toString().padStart(2, '0')}:${endTask.minute.toString().padStart(2, '0')}`,
        days: displayDays,
        taskIds: [task.id, pairedTask.id],
        enabled: task.enabled && pairedTask.enabled,
        params: startTask.params, // Use start task params for categories/bandwidth info
        categories: startTask.params?.categories,
        downloadMbps: startTask.params?.download_mbps,
        uploadMbps: startTask.params?.upload_mbps,
        spansMidnight
      });
      
      processedTaskIds.add(task.id);
      processedTaskIds.add(pairedTask.id);
    } else {
      // Single task with group - show as individual task
      const isInterval = task.task_type === 'interval';
      rules.push({
        id: `single_${task.id}`,
        type: service === 'agh' ? 'content' : 'bandwidth',
        groupId,
        service,
        task: task.task,
        startTime: isInterval ? null : `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
        endTime: null,
        days: days_of_week || [0,1,2,3,4,5,6],
        taskIds: [task.id],
        enabled: task.enabled,
        params: task.params,
        isInterval,
        intervalMinutes: task.interval_minutes,
        categories: task.params?.categories,
        downloadMbps: task.params?.download_mbps,
        uploadMbps: task.params?.upload_mbps
      });
      processedTaskIds.add(task.id);
    }
  }
  
  return rules;
};
